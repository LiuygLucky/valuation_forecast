from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from forecast.audit.hashing import sha256
from forecast.db.models import Observation
from forecast.domain.time_policy import ET, utc
from forecast.ingestion.versioning import save_source
from forecast.providers.npm_browser import read_capture


def ingest_capture(session, manifest_path: Path, *, now=None):
    record, text = read_capture(manifest_path)
    captured = utc(record["captured_at"])
    now = utc(now) if now else datetime.now(UTC)
    if captured > now:
        raise ValueError("NPM_CAPTURE_IN_FUTURE")
    digest = sha256(manifest_path.read_bytes())
    sid, vid = save_source(
        session,
        url=record["url"],
        publisher="Nasdaq Private Market",
        source_type="official_primary",
        seen_at=now,
        published_at=captured,
        content=text,
        title="OpenAI NPM browser capture: " + record["effective_date"],
        content_digest=digest,
        archive_uri=str(manifest_path.resolve()),
        metadata={
            "artifact_sha256": digest,
            "capture_method": "public_browser",
            "captured_at": record["captured_at"],
            "effective_date": record["effective_date"],
            "effective_timestamp_precision": "date",
            "page_artifacts": record["artifacts"],
            "public_time_basis": record["public_time_basis"],
            "verification": "DOM identity + metric/date parse + archive hashes; not an official API",
        },
    )
    existing = session.scalar(select(Observation).where(Observation.source_version_id == vid))
    if existing:
        return {"obs_id": existing.obs_id, "source_id": sid, "version_id": vid, "duplicate": True}
    obs_id = str(uuid4())
    session.add(
        Observation(
            obs_id=obs_id,
            metric_name="npm_valuation",
            value=record["valuation_trillion"],
            unit="USD_trillion",
            observed_at=captured.isoformat(),
            asof_et=captured.astimezone(ET).isoformat(),
            effective_date=record["effective_date"],
            source_version_id=vid,
            quality_flag="VERIFIED",
            observation_status="VERIFIED",
            methodology="NPM indicative Valuation; rendered page; effective time known only to date",
            ingestion_method="public_browser",
            provider="NPM",
            operator="NpmBrowserProvider",
            reviewer="deterministic_dom_and_artifact_verifier_v1",
            indicative=True,
            synthetic=False,
        )
    )
    return {"obs_id": obs_id, "source_id": sid, "version_id": vid, "duplicate": False}
