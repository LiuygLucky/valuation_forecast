import csv
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from forecast.audit.hashing import sha256
from forecast.config import load_config
from forecast.db.models import Observation
from forecast.domain.schemas import NpmObservation
from forecast.domain.time_policy import ET, utc
from forecast.ingestion.versioning import save_source


def import_observation(session, observation: NpmObservation, raw_dir: Path, *, ingested_at=None):
    cfg = load_config()
    if observation.url != cfg.metric_url:
        raise ValueError("NPM metric URL must match frozen task")
    if observation.synthetic:
        raise ValueError("manual real-data importer does not accept synthetic data")
    ingested_at = utc(ingested_at) if ingested_at else datetime.now(UTC)
    if utc(observation.captured_at) > ingested_at:
        raise ValueError("capture cannot be in the future")
    artifact = Path(observation.artifact_path).resolve()
    content = artifact.read_bytes()
    if not content:
        raise ValueError("empty evidence file")
    digest = sha256(content)
    raw_dir.mkdir(parents=True, exist_ok=True)
    target = raw_dir / (digest + artifact.suffix.lower())
    if not target.exists():
        with target.open("xb") as f:
            f.write(content)
    sid, vid = save_source(
        session,
        url=observation.url,
        publisher="Nasdaq Private Market",
        source_type="official_primary",
        seen_at=ingested_at,
        published_at=observation.observed_at,
        content=digest,
        title=f"Manual NPM capture {observation.observed_on}",
        archive_uri=str(target),
        content_digest=digest,
        archive_capture_at=(
            observation.archive_capture_at.isoformat() if observation.archive_capture_at else None
        ),
        archive_verified=observation.archive_verified,
        metadata={
            "artifact_sha256": digest,
            "operator": observation.operator,
            "reviewer": observation.reviewer,
            "page_content_sha256": digest,
            "manual_captured_at": utc(observation.captured_at).isoformat(),
        },
    )
    obs_id = str(uuid4())
    session.add(
        Observation(
            obs_id=obs_id,
            metric_name="npm_valuation",
            value=str(observation.valuation_trillion),
            unit="USD_trillion",
            observed_at=utc(observation.observed_at).isoformat(),
            asof_et=observation.observed_at.astimezone(ET).isoformat(),
            effective_date=(observation.effective_date or observation.observed_on).isoformat(),
            source_version_id=vid,
            quality_flag=observation.review_status,
            observation_status=observation.review_status,
            methodology=observation.methodology,
            ingestion_method=observation.ingestion_method,
            provider="NPM",
            operator=observation.operator,
            reviewer=observation.reviewer,
            indicative=observation.indicative,
            synthetic=False,
        )
    )
    return {"obs_id": obs_id, "source_id": sid, "version_id": vid, "artifact_sha256": digest}


def import_csv(session, csv_path: Path, raw_dir: Path):
    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8-sig").splitlines()))
    parsed = []
    for row in rows:
        row = {k: v for k, v in row.items() if v != ""}
        path = Path(row["artifact_path"])
        if not path.is_absolute():
            row["artifact_path"] = str(csv_path.resolve().parent / path)
        parsed.append(NpmObservation.model_validate(row))
    # Caller owns one transaction; malformed rows cannot leave a partial DB import.
    return [import_observation(session, row, raw_dir) for row in parsed]
