from forecast.causal.dag import validate_dag


def map_clusters(clusters, dag):
    validate_dag(dag)
    result = []
    for row in clusters:
        claim = row["claim"]
        allowed = dag["mechanisms"]
        mechanisms = claim["causal_mechanisms"]
        valid = all(
            m in allowed and claim["claim_type"] in allowed[m]["claim_types"] for m in mechanisms
        )
        paths = sorted({p for m in mechanisms if m in allowed for p in allowed[m]["path"]})
        drivers = {d for m in mechanisms if m in allowed for d in allowed[m]["drivers"]}
        valid = (
            valid
            and set(claim.get("mechanism_path_ids", [])) <= set(paths)
            and set(claim.get("drivers", [])) <= drivers
        )
        group = None
        if valid:
            if claim["claim_type"].startswith("financing"):
                state = claim["event_status"]
                group = "financing_" + ("cancelled" if state == "expired" else state)
            else:
                group = "growth_reported" if claim["claim_type"] == "revenue" else "cost_reported"
        result.append(
            row
            | {
                "likelihood_group_id": group,
                "mechanism_path_ids": paths,
                "causal_validation": "causal_effect_not_identified",
                "exclusion_reason": row.get("exclusion_reason")
                or (None if valid else "UNREGISTERED_MECHANISM"),
            }
        )
    return result
