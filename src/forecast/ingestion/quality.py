from forecast.domain.time_policy import utc


def coverage_matrix(inputs, as_of):
    rows = []
    for observation in inputs["observations"]:
        rows.append(
            {
                "field": observation["metric_name"],
                "effective_date": observation["effective_date"],
                "source_version_id": observation["source_version_id"],
                "quality": observation["quality_flag"],
                "unit": observation["unit"],
                "age_days": (utc(as_of) - utc(observation["observed_at"])).total_seconds() / 86400,
            }
        )
    for feature in inputs["features"]:
        rows.append(
            {
                "field": feature["feature_type"],
                "effective_date": feature["reference_period"],
                "source_version_id": feature["source_version_id"],
                "quality": feature["quality_flag"],
                "unit": feature["unit"],
            }
        )
    existing = {r["field"] for r in rows}
    for field in (
        "npm_valuation",
        "annual_revenue",
        "ARR",
        "cash_burn",
        "completed_financing",
        "market_risk",
    ):
        if field not in existing:
            rows.append({"field": field, "quality": "DATA_UNAVAILABLE"})
    return rows
