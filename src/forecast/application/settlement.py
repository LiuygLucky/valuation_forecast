from datetime import UTC, datetime, time
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from forecast.audit.hashing import sha256
from forecast.config import load_config
from forecast.db.models import (
    EvaluationScore,
    Observation,
    PredictionBin,
    PredictionRunRecord,
    Settlement,
    SourceVersion,
)
from forecast.db.session import init_db
from forecast.domain.bins import classify
from forecast.domain.time_policy import ET, local_time, utc
from forecast.evaluation.metrics import score


def settle(
    *,
    valuation=None,
    source_id=None,
    target_date="2026-12-31",
    confirm_final_observation=False,
    method_note="",
    now=None,
    engine=None,
):
    from pathlib import Path

    cfg = load_config()
    if target_date != str(cfg.settlement_target_date):
        raise ValueError("fixed settlement target date")
    now = utc(now) if now else datetime.now(UTC)
    if now < local_time(cfg.settlement_target_date):
        raise ValueError("SETTLEMENT_NOT_YET_ALLOWED")
    engine = init_db(engine)
    settlement_id = str(uuid4())
    with Session(engine) as session, session.begin():
        eligible = []
        end = utc(datetime.combine(cfg.settlement_target_date, time.max, ET))
        for obs, version in session.execute(select(Observation, SourceVersion).join(SourceVersion)):
            if (
                obs.quality_flag == "VERIFIED"
                and not obs.synthetic
                and obs.metric_name == "npm_valuation"
                and obs.effective_date <= target_date
                and utc(obs.observed_at) <= end
                and utc(version.captured_at) <= now
                and version.archive_uri
            ):
                artifact = Path(version.archive_uri)
                expected = version.metadata_json.get("artifact_sha256")
                if artifact.is_file() and expected and sha256(artifact.read_bytes()) == expected:
                    eligible.append((obs, version))
        eligible.sort(key=lambda pair: (pair[0].observed_at, pair[1].captured_at))
        chosen = eligible[-1] if eligible else None
        resolved = bool(chosen and confirm_final_observation and method_note.strip())
        if resolved and chosen is not None:
            obs, version = chosen
            if source_id not in (version.source_id, version.version_id):
                raise ValueError("SETTLEMENT_SOURCE_IS_NOT_LATEST_QUALIFIED_OBSERVATION")
            if valuation is None or Decimal(str(valuation)) != Decimal(obs.value):
                raise ValueError("SETTLEMENT_VALUE_MISMATCH")
        row = Settlement(
            settlement_id=settlement_id,
            task_id=cfg.task_id,
            target_date=target_date,
            observed_value=chosen[0].value if resolved and chosen else None,
            source_version_id=chosen[1].version_id if resolved and chosen else None,
            observed_at=now.isoformat(),
            settlement_effective_date=chosen[0].effective_date if resolved and chosen else None,
            status="RESOLVED" if resolved else "UNRESOLVED",
            bin_id=classify(chosen[0].value) if resolved and chosen else None,
            method_note=method_note
            or "Final eligible NPM observation cannot be confirmed; no scoring.",
        )
        session.add(row)
        session.flush()
        scores = []
        if resolved:
            for run in session.scalars(
                select(PredictionRunRecord).where(
                    PredictionRunRecord.status == "COMPLETED", PredictionRunRecord.mode == "LIVE"
                )
            ):
                assert run.completed_at is not None
                if utc(run.as_of_utc) > cfg.freeze_utc or utc(run.completed_at) > cfg.freeze_utc:
                    continue
                # Only actually sealed prospective LIVE runs qualify for official target scoring.
                if any(w.startswith("STORED_AS_OF_ONLY") for w in run.warnings_json):
                    continue
                bins = session.scalars(
                    select(PredictionBin).where(PredictionBin.run_id == run.run_id)
                )
                assert row.bin_id is not None
                values = score({b.bin_id: b.posterior_probability for b in bins}, row.bin_id)
                session.add(
                    EvaluationScore(
                        score_id=str(uuid4()),
                        run_id=run.run_id,
                        settlement_id=settlement_id,
                        evaluation_version="v1-epsilon-1e-12",
                        **values,
                    )
                )
                scores.append({"run_id": run.run_id, **values})
        return {
            "settlement_id": settlement_id,
            "status": row.status,
            "bin_id": row.bin_id,
            "effective_date": row.settlement_effective_date,
            "scores": scores,
        }
