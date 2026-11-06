def classify_scenario(
    *,
    financing_closed: bool,
    financing_amount: float,
    verified_revaluation: bool,
    repricing_fraction: float,
    config: dict,
) -> str:
    if (
        financing_closed
        and verified_revaluation
        and financing_amount >= config["major_financing_usd_trillion"]
    ):
        return "S1"
    if abs(repricing_fraction) >= config["major_repricing_threshold"]:
        return "S2"
    return "S3"
