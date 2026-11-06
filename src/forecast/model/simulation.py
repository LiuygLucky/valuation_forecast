import numpy as np

from forecast.domain.bins import bin_probs


def mix_samples(samples: dict[str, np.ndarray], weights: dict[str, float], seed: int):
    keys = sorted(samples)
    n = len(samples[keys[0]])
    rng = np.random.default_rng(seed)
    chosen = rng.choice(len(keys), n, p=[weights[k] for k in keys])
    indices = rng.integers(0, n, n)
    stacked = np.array([samples[k] for k in keys])
    return stacked[chosen, indices]


def summarize(samples):
    a = np.asarray(samples)
    return {
        "q05": float(np.quantile(a, 0.05)),
        "median": float(np.median(a)),
        "q95": float(np.quantile(a, 0.95)),
        "bin_probs": bin_probs(a),
    }
