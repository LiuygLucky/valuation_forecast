from decimal import Decimal

import numpy as np

BIN_IDS = ("B1", "B2", "B3", "B4", "B5", "B6")
EDGES = tuple(Decimal(x) for x in ("0.85", "1.00", "1.15", "1.30", "1.45"))


def classify(value: Decimal | float | str) -> str:
    v = Decimal(str(value))
    if not v.is_finite() or v <= 0:
        raise ValueError("valuation must be positive and finite")
    for i, edge in enumerate(EDGES):
        if v < edge or (i == 4 and v == edge):
            return BIN_IDS[i]
    return "B6"


def validate_probabilities(probs: dict[str, float]) -> dict[str, float]:
    if set(probs) != set(BIN_IDS):
        raise ValueError("all six bins required")
    a = np.array(list(probs.values()), dtype=np.float64)
    if not np.isfinite(a).all() or (a < 0).any() or abs(float(a.sum()) - 1) >= 1e-10:
        raise ValueError("invalid probability distribution")
    return probs


def bin_probs(samples: np.ndarray) -> dict[str, float]:
    a = np.asarray(samples, dtype=np.float64)
    if not a.size or not np.isfinite(a).all() or (a <= 0).any():
        raise ValueError("samples must be positive, finite and nonempty")
    indices = np.searchsorted(np.array(EDGES, dtype=float), a, side="right")
    indices[a == 1.45] = 4
    counts = np.bincount(indices, minlength=6) / a.size
    return validate_probabilities(dict(zip(BIN_IDS, counts.tolist(), strict=True)))
