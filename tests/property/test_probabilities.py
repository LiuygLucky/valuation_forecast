import numpy as np

from forecast.domain.bins import bin_probs, classify, validate_probabilities


def test_positive_domain_exhaustive_random_samples():
    rng = np.random.default_rng(90210)
    values = np.exp(rng.normal(0, 3, 10000))
    counts = {f"B{i}": 0 for i in range(1, 7)}
    for v in values:
        counts[classify(v)] += 1
    expected = {k: v / len(values) for k, v in counts.items()}
    assert bin_probs(values) == expected
    validate_probabilities(expected)
