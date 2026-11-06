from sqlalchemy import select, text

from forecast.db.models import ClaimRecord, FinancialFeature, Observation, Source, SourceVersion
from forecast.domain.time_policy import availability_reason, utc


def row_dict(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def freeze_inputs(session, as_of, *, provisional=False, archived=False):
    # Explicit BEGIN is necessary: Python sqlite legacy SELECT does not start a transaction.
    if not session.in_transaction():
        session.execute(text("BEGIN"))
    sources = {}
    for source, version in session.execute(select(Source, SourceVersion).join(SourceVersion)):
        data = row_dict(source) | row_dict(version)
        data["availability_reason"] = availability_reason(data, as_of, archived)
        sources[version.version_id] = data
    observations = []
    for obs in session.scalars(select(Observation)):
        src = sources[obs.source_version_id]
        quality = obs.quality_flag == "VERIFIED" or provisional
        if (
            not obs.synthetic
            and not src["synthetic"]
            and quality
            and src["availability_reason"] is None
            and utc(obs.observed_at) <= utc(as_of)
            and obs.metric_name == "npm_valuation"
            and obs.unit == "USD_trillion"
        ):
            observations.append(
                row_dict(obs) | {"source_id": src["source_id"], "captured_at": src["captured_at"]}
            )
    observations.sort(key=lambda x: (x["observed_at"], x["captured_at"], x["obs_id"]))
    features = []
    for feature in session.scalars(select(FinancialFeature)):
        src = sources[feature.source_version_id]
        if (
            not src["synthetic"]
            and not src["availability_reason"]
            and feature.quality_flag == "VERIFIED"
            and utc(feature.first_public_at) <= utc(as_of)
            and utc(feature.first_seen_at) <= utc(as_of)
        ):
            features.append(row_dict(feature))
    claims = []
    for claim in session.scalars(select(ClaimRecord)):
        src = sources[claim.source_version_id]
        if not src["synthetic"]:
            claims.append(row_dict(claim) | {"source": src})
    return {
        "anchor": observations[-1] if observations else None,
        "observations": observations,
        "features": features,
        "claims": claims,
        "sources": list(sources.values()),
    }
