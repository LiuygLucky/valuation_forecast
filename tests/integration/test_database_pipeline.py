from pathlib import Path

import httpx
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from forecast.application.pipeline import forecast_once, replay_run
from forecast.application.settlement import settle
from forecast.audit.hashing import sha256
from forecast.config import load_config
from forecast.db.models import Observation, PredictionRunRecord, SourceVersion
from forecast.db.queries import freeze_inputs
from forecast.db.session import init_db
from forecast.domain.schemas import NpmObservation
from forecast.ingestion.versioning import save_source
from forecast.providers.base import DataFetchResult
from forecast.providers.npm_manual import import_observation


def add_observation(engine, tmp_path, value="1.20", status="VERIFIED", day="2026-10-30"):
    artifact = tmp_path / (day + ".txt")
    artifact.write_text("SYNTHETIC TEST ARTIFACT, isolated test database only: " + day)
    observation = NpmObservation(
        observed_on=day,
        valuation_trillion=value,
        observed_at=f"{day}T13:00:00-04:00" if day < "2026-11" else f"{day}T13:00:00-05:00",
        captured_at=f"{day}T18:05:00Z",
        url=load_config().metric_url,
        artifact_path=str(artifact),
        operator="isolated_test",
        reviewer="isolated_test",
        review_status=status,
        methodology="synthetic test of manual ingestion",
    )
    with Session(engine) as session, session.begin():
        return import_observation(
            session, observation, tmp_path / "raw", ingested_at=observation.captured_at
        )


def test_repeatable_migration_immutable_versions(engine, tmp_path):
    init_db(engine)
    with engine.connect() as conn:
        assert conn.scalar(text("PRAGMA foreign_keys")) == 1
        assert conn.scalar(text("PRAGMA journal_mode")) == "wal"
    add_observation(engine, tmp_path)
    with Session(engine) as session, session.begin():
        first = session.scalar(select(SourceVersion))
        _, revision = save_source(
            session,
            url=load_config().metric_url,
            publisher="NPM",
            source_type="official_primary",
            seen_at="2026-11-03T20:00:00Z",
            published_at="2026-11-03T19:00:00Z",
            content="revised test",
            title="revision",
        )
        assert revision != first.version_id
    with Session(engine) as session:
        inputs = freeze_inputs(session, "2026-11-01T00:00:00Z")
        assert inputs["anchor"]["value"] == "1.20"
        assert any(s["availability_reason"] == "EXCLUDED_FUTURE" for s in inputs["sources"])
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("UPDATE source_versions SET title='edited'"))
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("DELETE FROM observations"))


def test_demo_replay_offline_and_no_overwrite(engine, tmp_path, monkeypatch):
    first = forecast_once(
        "2026-11-07T12:00:00-05:00", "DEMO", engine=engine, output_dir=tmp_path / "snapshots"
    )
    assert first.status == "COMPLETED"
    report = Path(first.snapshot_path) / "report.md"
    before = sha256(report.read_bytes())
    second = forecast_once(
        "2026-11-07T12:00:00-05:00", "DEMO", engine=engine, output_dir=tmp_path / "snapshots"
    )
    assert second.run_id != first.run_id
    assert sha256(report.read_bytes()) == before
    assert "DEMO / SYNTHETIC" in report.read_text(encoding="utf-8").splitlines()[0]

    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden during replay")

    monkeypatch.setattr(httpx.Client, "request", forbidden)
    replay = replay_run(first.run_id, engine=engine)
    assert replay.status == "REPRODUCED"
    assert replay.result == first.result
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(Observation)) == 0
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(
            text("UPDATE prediction_runs SET status='RUNNING' WHERE run_id=:id"),
            {"id": first.run_id},
        )


def test_live_no_synthetic_and_provisional(engine, tmp_path):
    forecast_once("2026-11-01T00:00:00Z", "DEMO", engine=engine, output_dir=tmp_path / "snapshots")
    missing = forecast_once(
        "2026-11-01T00:00:00Z", "LIVE", engine=engine, output_dir=tmp_path / "snapshots"
    )
    assert missing.status == "NO_VALID_ANCHOR"
    add_observation(engine, tmp_path, status="UNVERIFIED")
    assert (
        forecast_once(
            "2026-11-01T00:00:00Z", "LIVE", engine=engine, output_dir=tmp_path / "snapshots"
        ).status
        == "NO_VALID_ANCHOR"
    )
    provisional = forecast_once(
        "2026-11-01T00:00:00Z", "PROVISIONAL", engine=engine, output_dir=tmp_path / "snapshots"
    )
    assert provisional.status == "COMPLETED"
    with Session(engine) as session:
        assert session.get(PredictionRunRecord, provisional.run_id).data_quality == "PROVISIONAL"


def test_disconnect_degrades_to_verified_baseline(engine, tmp_path):
    add_observation(engine, tmp_path)

    class FailedSearch:
        def search(self, *args, **kwargs):
            return DataFetchResult("Tavily", "SEARCH_FAILURE", reason="TEST_DISCONNECTED")

    result = forecast_once(
        mode="LIVE",
        engine=engine,
        output_dir=tmp_path / "snapshots",
        providers={"search": FailedSearch()},
    )
    assert result.status == "COMPLETED"
    assert any("SEARCH_FAILURE" in w for w in result.warnings)
    assert any("BASELINE_ONLY" in w for w in result.warnings)
    assert any("NPM_FETCH_BLOCKED" in w for w in result.warnings)


def test_settlement_boundary_and_unresolved(engine, tmp_path):
    with pytest.raises(ValueError, match="NOT_YET_ALLOWED"):
        settle(now="2026-12-30T00:00:00Z", engine=engine)
    unresolved = settle(now="2027-01-01T00:00:00Z", engine=engine)
    assert unresolved["status"] == "UNRESOLVED" and not unresolved["scores"]
    imported = add_observation(engine, tmp_path, value="1.45", day="2026-12-31")
    resolved = settle(
        valuation="1.45",
        source_id=imported["source_id"],
        confirm_final_observation=True,
        method_note="Isolated test final capture",
        now="2027-01-01T00:00:00Z",
        engine=engine,
    )
    assert resolved["status"] == "RESOLVED" and resolved["bin_id"] == "B5"
    with pytest.raises(ValueError, match="VALUE_MISMATCH"):
        settle(
            valuation="1.4",
            source_id=imported["source_id"],
            confirm_final_observation=True,
            method_note="test",
            now="2027-01-01T00:00:00Z",
            engine=engine,
        )


def test_failure_record_and_freeze(engine, tmp_path):
    result = forecast_once(
        "2027-01-01T00:00:00Z", "DEMO", engine=engine, output_dir=tmp_path / "snapshots"
    )
    assert result.status == "PREDICTION_FROZEN"
    with Session(engine) as session:
        run = session.get(PredictionRunRecord, result.run_id)
        assert run.status == "FAILED" and run.completed_at
    assert (
        forecast_once("2026-11-01T00:00:00Z", "HISTORICAL_ARCHIVED", engine=engine).status
        == "ARCHIVE_REQUIRED"
    )
