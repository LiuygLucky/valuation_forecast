import math

import numpy as np

from forecast.domain.bins import BIN_IDS, validate_probabilities


def score(probabilities: dict, observed_bin: str):
    validate_probabilities(probabilities)
    index = BIN_IDS.index(observed_bin)
    p = np.array([probabilities[k] for k in BIN_IDS])
    y = np.eye(6)[index]
    return {
        "brier": float(np.square(p - y).sum()),
        "log_loss": -math.log(max(float(p[index]), 1e-12)),
        "rps": float(np.square(np.cumsum(p)[:-1] - np.cumsum(y)[:-1]).sum()),
    }


def calibration(records, min_samples=100, bins=10):
    if len(records) < min_samples:
        return {"status": "INSUFFICIENT_SAMPLES", "n": len(records), "ece": None, "buckets": []}
    # Top-label ECE, with explicit bucket counts; distinct from per-class calibration.
    confidence, correct = [], []
    for row in records:
        p = validate_probabilities(row["probabilities"])
        predicted = max(p, key=lambda k: p[k])
        confidence.append(p[predicted])
        correct.append(float(predicted == row["observed_bin"]))
    buckets, ece = [], 0.0
    for i in range(bins):
        indices = [j for j, c in enumerate(confidence) if min(int(c * bins), bins - 1) == i]
        if indices:
            avg = float(np.mean([confidence[j] for j in indices]))
            accuracy = float(np.mean([correct[j] for j in indices]))
            ece += len(indices) / len(records) * abs(avg - accuracy)
            buckets.append(
                {
                    "lower": i / bins,
                    "upper": (i + 1) / bins,
                    "n": len(indices),
                    "mean_confidence": avg,
                    "accuracy": accuracy,
                }
            )
        else:
            buckets.append({"lower": i / bins, "upper": (i + 1) / bins, "n": 0})
    return {
        "status": "DESCRIPTIVE_ONLY",
        "method": "top-label ECE",
        "n": len(records),
        "ece": ece,
        "buckets": buckets,
    }
