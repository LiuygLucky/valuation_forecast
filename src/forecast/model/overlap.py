from forecast.domain.time_policy import utc


def detect_overlap(cluster: dict, anchor: dict, structured_version_ids: set[str], alpha: float):
    if cluster.get("exclusion_reason"):
        return {
            "overlap_status": cluster["exclusion_reason"],
            "alpha": 0.0,
            "effect_channel": "explanation_only",
        }
    if set(cluster["source_version_ids"]) & structured_version_ids:
        return {
            "overlap_status": "baseline_input_overlap",
            "alpha": 0.0,
            "effect_channel": "explanation_only",
        }
    if utc(cluster["first_public_at"]) <= utc(anchor["observed_at"]):
        return {
            "overlap_status": "PARTIALLY_OR_POSSIBLY_ABSORBED",
            "alpha": 0.0,
            "effect_channel": "explanation_only",
        }
    return {
        "overlap_status": "NEW_INFORMATION",
        "alpha": alpha,
        "effect_channel": "scenario_weight",
    }
