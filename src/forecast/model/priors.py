import math


def validate_priors(priors: dict) -> dict:
    if priors["nu"] <= 2:
        raise ValueError("Student-t requires nu > 2")
    if priors["h_floor"] < 0 or (priors["h_floor"] and not priors["quote_error_verified"]):
        raise ValueError("h_floor requires verified quote error")
    weights = priors["scenario_weights"]
    if set(weights) != {"S1", "S2", "S3"} or any(w <= 0 for w in weights.values()):
        raise ValueError("three positive scenario weights required")
    if not math.isclose(sum(weights.values()), 1, abs_tol=1e-12):
        raise ValueError("scenario weights must sum to one")
    for params in priors["scenarios"].values():
        for key in ("mu", "sigma", "jump", "pass_through", "lag_days"):
            lo, hi = params[key]
            if not math.isfinite(lo + hi) or lo > hi:
                raise ValueError("invalid parameter range")
        if params["sigma"][0] < 0 or params["lag_days"][0] < 0:
            raise ValueError("negative scale or lag")
        if not 0 <= params["pass_through"][0] <= params["pass_through"][1] <= 1:
            raise ValueError("invalid pass-through")
    return priors
