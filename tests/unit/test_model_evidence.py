from copy import deepcopy

import numpy as np
import pytest

from forecast.agent.event_state import compare_claims, valid_transition
from forecast.application.pipeline import calculate
from forecast.causal.dag import validate_dag
from forecast.causal.scenario_registry import classify_scenario
from forecast.config import load_config, load_yaml
from forecast.domain.bins import validate_probabilities
from forecast.ingestion.source_graph import build_clusters
from forecast.model.baseline import compute_baseline
from forecast.model.likelihoods import build_likelihoods
from forecast.model.overlap import detect_overlap
from forecast.model.posterior import compute_posterior, update_scenarios
from forecast.model.priors import validate_priors

AS_OF = "2026-11-07T17:00:00+00:00"


def calculation(inputs):
    return calculate(
        inputs,
        AS_OF,
        load_config(),
        load_yaml("model_priors.yaml"),
        load_yaml("evidence_likelihoods.yaml"),
        load_yaml("causal_graph.yaml"),
        "DEMO",
    )


def test_deterministic_valid_mixture_and_sensitivity(demo):
    b, e, p, sensitivity = calculation(demo)
    assert calculation(demo)[2] == p
    validate_probabilities(b["prior_bin_probs"])
    validate_probabilities(p["bin_probabilities"])
    assert sum(p["scenario_posterior"].values()) == pytest.approx(1)
    for probs in sensitivity.values():
        validate_probabilities(probs)
    assert sensitivity["high"] != sensitivity["low"]
    assert sensitivity["prior_sigma_low"] != sensitivity["prior_sigma_high"]
    assert p["parameter_uncertainty_interval"] is None
    assert len(p["posterior_samples"]) == 20000
    assert np.min(p["posterior_samples"]) > 0
    assert all(v > 0 for v in p["mc_se"].values())


def test_reuters_plus_three_syndications_one_update(demo):
    original = demo["claims"][0]
    original["source"]["publisher"] = "Reuters (synthetic test)"
    demo["claims"] = [original]
    expected = calculation(demo)[2]["bin_probabilities"]
    for i in range(3):
        copy = deepcopy(original)
        copy["claim_id"] = f"syndicated_{i}"
        copy["source"]["source_id"] = f"syndicated_source_{i}"
        copy["source"]["version_id"] = f"syndicated_version_{i}"
        copy["source"]["parent_source_id"] = original["source"]["source_id"]
        copy["source"]["source_type"] = "syndicated"
        demo["claims"].append(copy)
    _, evidence, posterior, _ = calculation(demo)
    assert len(evidence) == 1
    assert evidence[0]["duplicate_count"] == 3
    assert posterior["bin_probabilities"] == expected


def test_delayed_reprint_does_not_evade_absorption(demo):
    original = demo["claims"][0]
    old = "2026-11-01T17:00:00+00:00"
    original["claim_json"]["published_at"] = old
    original["source"].update(
        published_at=old, first_public_at=old, first_seen_at=old, captured_at=old
    )
    reprint = deepcopy(original)
    reprint["claim_id"] = "later_reprint"
    reprint["claim_json"]["published_at"] = "2026-11-06T17:00:00+00:00"
    demo["claims"] = [original, reprint]
    baseline, evidence, posterior, _ = calculation(demo)
    assert evidence[0]["alpha"] == 0
    assert posterior["bin_probabilities"] == pytest.approx(baseline["prior_bin_probs"])


def test_state_as_of_and_corrections(demo):
    proposed = demo["claims"][0]
    closed = deepcopy(proposed)
    closed["claim_id"] = "closed"
    closed["claim_json"]["event_status"] = "closed"
    later = "2026-11-08T17:00:00+00:00"
    closed["claim_json"]["published_at"] = later
    closed["source"].update(
        published_at=later, first_public_at=later, first_seen_at=later, captured_at=later
    )
    early = build_clusters([proposed, closed], AS_OF)
    active = [c for c in early if not c["exclusion_reason"]]
    assert active[0]["claim"]["event_status"] == "proposed"
    late = build_clusters([proposed, closed], "2026-11-09T00:00:00Z")
    assert len(late) == 1 and late[0]["claim"]["event_status"] == "closed"
    assert not valid_transition("closed", "proposed")
    assert valid_transition("closed", "corrected")
    assert not valid_transition("cancelled", "closed")
    assert valid_transition("proposed", "cancelled")
    corrected = deepcopy(closed)
    corrected["claim_id"] = "corrected"
    corrected["claim_json"]["event_status"] = "corrected"
    corrected["claim_json"]["published_at"] = "2026-11-08T19:00:00Z"
    assert (
        build_clusters([proposed, closed, corrected], "2026-11-09T00:00:00Z")[0]["exclusion_reason"]
        == "REVIEW_REQUIRED"
    )


def test_scope_conflicts_and_invalid_verification(demo):
    a = demo["claims"][0]["claim_json"]
    assert compare_claims(a, a | {"valuation_basis": "pre_money"}) == "NON_CONFLICT_DIFFERENT_SCOPE"
    assert compare_claims(a, a | {"reported_valuation_trillion": "1.3"}) == "CONTRADICTS"
    bad = deepcopy(demo["claims"][0])
    bad["claim_id"] = "conflict"
    bad["claim_json"]["reported_valuation_trillion"] = "1.3"
    assert (
        build_clusters([demo["claims"][0], bad], AS_OF)[0]["exclusion_reason"] == "REVIEW_REQUIRED"
    )
    bad["verification_status"] = "VALUE_NOT_SUPPORTED"
    assert build_clusters([bad], AS_OF)[0]["exclusion_reason"] == "REVIEW_REQUIRED"


def test_overlap_guard_and_channels(demo):
    cluster = build_clusters([demo["claims"][0]], AS_OF)[0]
    overlap = detect_overlap(cluster, demo["anchor"], set(cluster["source_version_ids"]), 0.35)
    assert overlap["alpha"] == 0 and overlap["overlap_status"] == "baseline_input_overlap"
    baseline, evidence, _, _ = calculation(demo)
    assert any(e["overlap_status"] == "EXCLUDED_FUTURE" for e in evidence)
    assert any(e["overlap_status"] == "PARTIALLY_OR_POSSIBLY_ABSORBED" for e in evidence)
    included = next(e for e in evidence if e["included"])
    with pytest.raises(ValueError, match="duplicate"):
        update_scenarios(baseline["scenario_prior"], [included, included])
    with pytest.raises(ValueError):
        update_scenarios(baseline["scenario_prior"], [included | {"alpha": 2}])
    with pytest.raises(ValueError):
        update_scenarios(
            baseline["scenario_prior"], [included | {"effect_channel": "conditional_value"}]
        )
    no_evidence = compute_posterior(baseline, [], load_config().seed)
    assert no_evidence["bin_probabilities"] == pytest.approx(baseline["prior_bin_probs"])


def test_unregistered_mechanism_and_likelihood(demo):
    demo["claims"][0]["claim_json"]["causal_mechanisms"] = ["invented_probability"]
    demo["claims"] = demo["claims"][:1]
    _, e, _, _ = calculation(demo)
    assert e[0]["alpha"] == 0
    lc = load_yaml("evidence_likelihoods.yaml")
    e[0].update(exclusion_reason=None, likelihood_group_id="financing_proposed")
    lc["groups"]["financing_proposed"]["S1"] = -1
    with pytest.raises(ValueError):
        build_likelihoods(e, demo["anchor"], [], lc)
    lc = load_yaml("evidence_likelihoods.yaml")
    lc["alpha"] = 2
    with pytest.raises(ValueError):
        build_likelihoods(e, demo["anchor"], [], lc)


@pytest.mark.parametrize(
    "change",
    [
        {"nu": 2},
        {"h_floor": 0.1},
        {"h_floor": -0.1},
        {"scenario_weights": {"S1": 0.5}},
        {"scenario_weights": {"S1": 0.2, "S2": 0.2, "S3": 0.2}},
    ],
)
def test_prior_validation(change):
    with pytest.raises(ValueError):
        validate_priors(load_yaml("model_priors.yaml") | change)


@pytest.mark.parametrize(
    "key,span",
    [("sigma", [-1, 2]), ("mu", [1, 0]), ("lag_days", [-1, 2]), ("pass_through", [0, 2])],
)
def test_invalid_ranges(key, span):
    p = load_yaml("model_priors.yaml")
    p["scenarios"]["S1"][key] = span
    with pytest.raises(ValueError):
        validate_priors(p)


def test_baseline_guardrails_and_dag(demo):
    cfg, p = load_config(), load_yaml("model_priors.yaml")
    with pytest.raises(ValueError):
        compute_baseline(demo["anchor"], "2027-01-01T00:00:00Z", cfg, p)
    with pytest.raises(ValueError):
        compute_baseline(demo["anchor"] | {"value": 0}, AS_OF, cfg, p)
    p["scenarios"]["S1"]["mu"] = [10000, 10000]
    with pytest.raises(ValueError, match="NUMERICAL_RANGE"):
        compute_baseline(demo["anchor"], AS_OF, cfg, p)
    dag = load_yaml("causal_graph.yaml")
    assert len(validate_dag(dag)) > 10
    dag["edges"].append(dag["edges"][0])
    with pytest.raises(ValueError):
        validate_dag(dag)
    p = load_yaml("model_priors.yaml")
    assert (
        classify_scenario(
            financing_closed=True,
            financing_amount=0.02,
            verified_revaluation=True,
            repricing_fraction=0.3,
            config=p,
        )
        == "S1"
    )
    assert (
        classify_scenario(
            financing_closed=False,
            financing_amount=0,
            verified_revaluation=False,
            repricing_fraction=-0.2,
            config=p,
        )
        == "S2"
    )
    assert (
        classify_scenario(
            financing_closed=False,
            financing_amount=0,
            verified_revaluation=False,
            repricing_fraction=0.01,
            config=p,
        )
        == "S3"
    )
