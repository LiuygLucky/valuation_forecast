import numpy as np

from forecast.domain.bins import BIN_IDS, validate_probabilities
from forecast.domain.schemas import BaselineOutput
from forecast.domain.time_policy import local_time, utc
from forecast.model.priors import validate_priors
from forecast.model.simulation import mix_samples, summarize


def compute_baseline(anchor: dict, as_of, cfg, priors: dict, quality="VERIFIED"):
    validate_priors(priors)
    cutoff = utc(as_of)
    remaining_days = (local_time(cfg.settlement_target_date) - cutoff).total_seconds() / 86400
    if remaining_days < 0:
        raise ValueError("prediction horizon cannot be negative")
    value = float(anchor["value"])
    if not np.isfinite(value) or value <= 0:
        raise ValueError("NO_VALID_ANCHOR")
    h = remaining_days / 365.25
    h_eff = max(h, priors["h_floor"])
    rng = np.random.default_rng(cfg.seed)
    samples, summaries = {}, {}
    n = cfg.monte_carlo_samples
    nu = priors["nu"]
    for sid, parameters in sorted(priors["scenarios"].items()):
        draws = {
            k: rng.uniform(parameters[k][0], parameters[k][1], size=n)
            for k in ("mu", "sigma", "jump", "pass_through", "lag_days")
        }
        noise = rng.standard_t(nu, n) * np.sqrt((nu - 2) / nu)
        # Latency suppresses shocks whose transmission would occur after settlement.
        shock = draws["jump"] * draws["pass_through"] * (draws["lag_days"] <= remaining_days)
        log_v = np.log(value) + draws["mu"] * h + draws["sigma"] * np.sqrt(h_eff) * noise + shock
        if not np.isfinite(log_v).all() or (np.abs(log_v) > 700).any():
            raise ValueError("NUMERICAL_RANGE: inspect prior assumptions")
        samples[sid] = np.exp(log_v)
        threshold = priors["direction_threshold_log"]
        summaries[sid] = summarize(samples[sid]) | {
            "revaluation_direction": {
                "up": float(np.mean(log_v - np.log(value) > threshold)),
                "down": float(np.mean(log_v - np.log(value) < -threshold)),
                "near_unchanged": float(np.mean(np.abs(log_v - np.log(value)) <= threshold)),
            }
        }
    weights = priors["scenario_weights"]
    # Stratified mixture integration avoids extra multinomial noise in displayed probabilities.
    probabilities = validate_probabilities(
        {k: sum(weights[s] * summaries[s]["bin_probs"][k] for s in samples) for k in BIN_IDS}
    )
    mixed = mix_samples(samples, weights, cfg.seed + 1)
    result = BaselineOutput(
        task_id=cfg.task_id,
        as_of_utc=cutoff,
        anchor_value_trillion=value,
        anchor_source_id=anchor["source_id"],
        samples_trillion=mixed.tolist(),
        prior_bin_probs=probabilities,
        scenario_prior=weights,
        scenario_params=priors["scenarios"],
        parameter_provenance={
            "origin_type": priors["origin_type"],
            "reviewer": priors["reviewer"],
            "basis": priors["basis"],
        },
        assumptions=[
            "heuristic; UNCALIBRATED",
            "beta=0; not identified",
            "causal_effect_not_identified",
            "NPM is an indicative metric",
        ],
        data_quality=quality,
    )
    return result.model_dump(mode="json") | {
        "conditional_summaries": summaries,
        "conditional_samples": {k: v.tolist() for k, v in samples.items()},
        "predictive_quantiles": summarize(mixed),
        "h_years": h,
        "anchor_age_days": (cutoff - utc(anchor["observed_at"])).total_seconds() / 86400,
    }
