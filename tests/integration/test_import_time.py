import pytest
from sqlalchemy.orm import Session

from forecast.application.input_validation import freeze_task_contract
from forecast.application.pipeline import forecast_once
from forecast.config import load_config
from forecast.db.queries import freeze_inputs
from forecast.domain.schemas import NpmObservation
from forecast.providers.npm_manual import import_observation


def test_importing_old_capture_does_not_backdate_first_seen(engine, tmp_path):
    file = tmp_path / "historical.txt"
    file.write_text("SYNTHETIC isolated regression artifact")
    obs = NpmObservation(
        observed_on="2026-10-01",
        valuation_trillion="1.2",
        observed_at="2026-10-01T17:00:00Z",
        captured_at="2026-10-01T18:00:00Z",
        url=load_config().metric_url,
        artifact_path=str(file),
        operator="test",
        review_status="VERIFIED",
        reviewer="test",
        methodology="isolated test",
    )
    with Session(engine) as session, session.begin():
        import_observation(session, obs, tmp_path / "raw", ingested_at="2026-11-01T00:00:00Z")
    with Session(engine) as session:
        assert freeze_inputs(session, "2026-10-15T00:00:00Z")["anchor"] is None
    with Session(engine) as session:
        assert freeze_inputs(session, "2026-11-02T00:00:00Z")["anchor"] is not None


def test_certified_archive_mode_replays_historical_visibility(engine, tmp_path):
    file = tmp_path / "certified.txt"
    file.write_text("SYNTHETIC archive proof in an isolated test database")
    observation = NpmObservation(
        observed_on="2026-10-30",
        valuation_trillion="1.20",
        observed_at="2026-10-30T17:00:00Z",
        captured_at="2026-10-30T18:00:00Z",
        archive_capture_at="2026-10-30T18:00:00Z",
        archive_verified=True,
        url=load_config().metric_url,
        artifact_path=str(file),
        operator="test",
        review_status="VERIFIED",
        reviewer="test",
        methodology="isolated archive test",
    )
    with Session(engine) as session, session.begin():
        import_observation(
            session, observation, tmp_path / "raw", ingested_at="2026-11-02T00:00:00Z"
        )
    with Session(engine) as session:
        assert freeze_inputs(session, "2026-11-01T00:00:00Z")["anchor"] is None
    with Session(engine) as session:
        frozen = freeze_inputs(session, "2026-11-01T00:00:00Z", archived=True)
    result = forecast_once(
        "2026-11-01T00:00:00Z",
        "HISTORICAL_ARCHIVED",
        engine=engine,
        output_dir=tmp_path / "snapshots",
        archived_inputs=frozen,
    )
    assert result.status == "COMPLETED"
    assert sum(result.result["bin_probabilities"].values()) == pytest.approx(1)


def test_task_contract_freeze(tmp_path):
    task = load_config().model_dump(mode="json")
    freeze_task_contract(tmp_path, task)
    freeze_task_contract(tmp_path, task)
    with pytest.raises(ValueError, match="FROZEN_TASK_CONFIG_CHANGED"):
        freeze_task_contract(tmp_path, task | {"seed": 123})
