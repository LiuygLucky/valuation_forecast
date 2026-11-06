import math

from forecast.model.overlap import detect_overlap


def build_likelihoods(clusters, anchor, features, config):
    used = {anchor["source_version_id"]} | {f["source_version_id"] for f in features}
    output = []
    for cluster in clusters:
        row = cluster | detect_overlap(cluster, anchor, used, config["alpha"])
        group = row.get("likelihood_group_id")
        likelihood = config["groups"].get(group)
        if likelihood is None:
            row.update(alpha=0.0, effect_channel="explanation_only")
            row["exclusion_reason"] = row.get("exclusion_reason") or "NO_APPROVED_LIKELIHOOD"
        elif set(likelihood) != {"S1", "S2", "S3"} or any(
            not math.isfinite(v) or not 0 < v <= 1 for v in likelihood.values()
        ):
            raise ValueError("invalid likelihood mapping")
        if not 0 <= row["alpha"] <= 1:
            raise ValueError("alpha must be in [0,1]")
        row["likelihood"] = likelihood
        row["included"] = row["alpha"] > 0
        row["parameter_origin"] = config["origin_type"]
        output.append(row)
    return output
