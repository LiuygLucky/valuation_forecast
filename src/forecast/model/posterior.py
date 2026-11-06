import numpy as np
from scipy.special import logsumexp

from forecast.domain.bins import BIN_IDS, validate_probabilities
from forecast.model.simulation import mix_samples, summarize


def update_scenarios(prior: dict, evidence: list[dict], strength: float = 1):
    keys = sorted(prior)
    log_w = np.log([prior[k] for k in keys])
    seen = set()
    for row in evidence:
        if row["cluster_id"] in seen:
            raise ValueError("duplicate cluster update forbidden")
        seen.add(row["cluster_id"])
        alpha = row["alpha"] * strength
        if not 0 <= alpha <= 1:
            raise ValueError("tempered likelihood alpha out of range")
        if alpha:
            if row["effect_channel"] != "scenario_weight":
                raise ValueError("single effect channel required")
            log_w += alpha * np.log([row["likelihood"][k] for k in keys])
    return dict(zip(keys, np.exp(log_w - logsumexp(log_w)).tolist(), strict=True))


def compute_posterior(baseline: dict, evidence: list[dict], seed: int, strength=1):
    weights = update_scenarios(baseline["scenario_prior"], evidence, strength)
    summaries = baseline["conditional_summaries"]
    probs = validate_probabilities(
        {k: sum(weights[s] * summaries[s]["bin_probs"][k] for s in weights) for k in BIN_IDS}
    )
    samples = {s: np.asarray(a) for s, a in baseline["conditional_samples"].items()}
    mixed = mix_samples(samples, weights, seed + 1)
    n = len(mixed)
    # Conditional samples are independently stratified by scenario.
    mc_se = {
        k: float(
            np.sqrt(
                sum(
                    weights[s] ** 2
                    * summaries[s]["bin_probs"][k]
                    * (1 - summaries[s]["bin_probs"][k])
                    / n
                    for s in weights
                )
            )
        )
        for k in BIN_IDS
    }
    return {
        "bin_probabilities": probs,
        "scenario_posterior": weights,
        "posterior_samples": mixed.tolist(),
        "mc_se": mc_se,
        "predictive_quantiles": summarize(mixed),
        "uncertainty_label": "MC SE only; parameters are heuristic, not calibrated",
        "parameter_uncertainty_interval": None,
    }


def sensitivity(baseline, evidence, seed):
    return {
        label: compute_posterior(baseline, evidence, seed, strength)["bin_probabilities"]
        for label, strength in (("no_evidence", 0), ("low", 0.5), ("base", 1), ("high", 2))
        if all(row["alpha"] * strength <= 1 for row in evidence)
    }
