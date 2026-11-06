from copy import deepcopy

from forecast.causal.scenario_assessor import map_clusters
from forecast.config import load_yaml
from forecast.ingestion.source_graph import build_clusters
from forecast.model.baseline import compute_baseline
from forecast.model.likelihoods import build_likelihoods
from forecast.model.posterior import compute_posterior


def ablation_predictions(task, priors=None):
    """Same frozen inputs, origin, seed and test cases; deliberately labeled research variants."""
    priors = deepcopy(priors or load_yaml("model_priors.yaml"))
    lc, dag = load_yaml("evidence_likelihoods.yaml"), load_yaml("causal_graph.yaml")
    cfg = type(
        "AuxiliaryConfig",
        (),
        {
            "task_id": task.task_id,
            "settlement_target_date": task.target_date,
            "seed": task.seed,
            "monte_carlo_samples": task.monte_carlo_samples,
        },
    )()
    inputs = task.inputs
    base = compute_baseline(inputs["anchor"], task.as_of, cfg, priors, task.experiment)
    m0_prior = deepcopy(priors)
    for params in m0_prior["scenarios"].values():
        params.update(mu=[0, 0], sigma=[0.35, 0.35], jump=[0, 0], pass_through=[0, 0])
    m0 = compute_baseline(inputs["anchor"], task.as_of, cfg, m0_prior, task.experiment)
    clusters = build_clusters(
        inputs["claims"], task.as_of, archived=task.experiment == "HISTORICAL_ARCHIVED"
    )
    mapped = map_clusters(clusters, dag)
    guarded = build_likelihoods(mapped, inputs["anchor"], inputs["features"], lc)
    m3, m4, sentiment = deepcopy(guarded), deepcopy(guarded), []
    for row in m4:
        if not row.get("exclusion_reason") and row.get("likelihood"):
            row.update(alpha=lc["alpha"], effect_channel="scenario_weight")
    for row in m3:
        if not row.get("exclusion_reason"):
            direction = row["claim"]["direction"]
            row.update(
                alpha=lc["alpha"],
                effect_channel="scenario_weight",
                likelihood={"S1": 0.6, "S2": 0.6, "S3": 0.4}
                if direction == "up"
                else {"S1": 0.4, "S2": 0.6, "S3": 0.6},
            )
    # M2 deliberately uses individual eligible news items with a naive lexical sign.
    # It is an ablation only and is never selectable by the main Dashboard.
    for row in inputs["claims"]:
        from forecast.domain.time_policy import availability_reason

        if availability_reason(row["source"], task.as_of, task.experiment == "HISTORICAL_ARCHIVED"):
            continue
        text = row["source"]["raw_excerpt"].lower()
        positive = any(w in text for w in ("growth", "investment", "closed", "revenue"))
        sentiment.append(
            {
                "cluster_id": row["claim_id"],
                "alpha": lc["alpha"],
                "effect_channel": "scenario_weight",
                "likelihood": {"S1": 0.6, "S2": 0.6, "S3": 0.4}
                if positive
                else {"S1": 0.4, "S2": 0.6, "S3": 0.6},
            }
        )
    variants = {
        "M0": (m0, []),
        "M1": (base, []),
        "M2": (base, sentiment),
        "M3": (base, m3),
        "M4": (base, m4),
        "M5": (base, guarded),
    }
    return {
        name: {
            "probabilities": compute_posterior(b, e, task.seed)["bin_probabilities"],
            "effective_evidence": sum(r["alpha"] > 0 for r in e),
            "calibration": "NOT_FITTED",
        }
        for name, (b, e) in variants.items()
    }
