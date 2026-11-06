"""Synthetic page fixtures remain confined to pytest's isolated directories/database."""

from pathlib import Path

import httpx
import pytest
from sqlalchemy.orm import Session

from forecast.application.pipeline import forecast_once, replay_run
from forecast.audit.snapshot import read_snapshot
from forecast.db.queries import freeze_inputs
from forecast.ingestion.npm_capture import ingest_capture
from forecast.model.overlap import detect_overlap
from forecast.providers.npm_browser import NpmBrowserProvider, parse_npm_text, read_capture

TEXT = "SYNTHETIC TEST\nPrivate Company Pricing by Nasdaq Private Market\nOpenAI\nAs of Nov 4, 2026\nValuation\n$1.281T\nPrice Per Share\n$1,016.68"
CAPTURED = "2026-11-06T20:00:00+00:00"


def bundle(tmp_path):
    result = NpmBrowserProvider(
        root=tmp_path / "captures",
        renderer=lambda url: {
            "url": url,
            "http_status": None,
            "capture_transport": "codex_browser",
            "text": TEXT,
            "html": "<p>SYNTHETIC TEST</p>",
            "screenshot": b"\xff\xd8\xffTEST",
            "captured_at": CAPTURED,
        },
    ).fetch_latest()
    assert result.status == "OK"
    return Path(result.data["capture_manifest"])


def test_parse_metric_date_and_fail_closed():
    parsed = parse_npm_text(TEXT, CAPTURED)
    assert parsed["valuation_trillion"] == "1.281"
    assert parsed["effective_date"] == "2026-11-04"
    assert parsed["captured_at"] == CAPTURED
    assert (
        parse_npm_text(TEXT.replace("1.281T", "1,281B"), CAPTURED)["valuation_trillion"] == "1.281"
    )
    for bad in (
        TEXT.replace("OpenAI", "Other"),
        TEXT.replace("Valuation", "PPS"),
        TEXT + "\nValuation\n$2T",
        TEXT.replace("Nov 4", "Nov 9"),
    ):
        with pytest.raises(ValueError):
            parse_npm_text(bad, CAPTURED)


def test_capture_ingestion_dates_idempotence_and_tampering(engine, tmp_path):
    path = bundle(tmp_path)
    with Session(engine) as session, session.begin():
        first = ingest_capture(session, path, now="2026-11-06T20:01:00Z")
    with Session(engine) as session, session.begin():
        second = ingest_capture(session, path, now="2026-11-06T20:02:00Z")
    assert first["obs_id"] == second["obs_id"] and second["duplicate"]
    with Session(engine) as session:
        assert freeze_inputs(session, "2026-11-05T23:00:00Z")["anchor"] is None
        anchor = freeze_inputs(session, "2026-11-06T20:02:00Z")["anchor"]
        assert anchor["effective_date"] == "2026-11-04"
        assert anchor["observed_at"] == CAPTURED
        assert anchor["effective_timestamp_precision"] == "date"
    (path.parent / "page.jpg").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="HASH_MISMATCH"):
        read_capture(path)


@pytest.mark.parametrize(
    "day,status",
    [
        ("03", "PARTIALLY_OR_POSSIBLY_ABSORBED"),
        ("04", "ANCHOR_TIME_UNCERTAIN"),
        ("05", "NEW_INFORMATION"),
    ],
)
def test_absorption_uses_effective_day_not_later_capture(day, status):
    anchor = {
        "effective_timestamp_precision": "date",
        "effective_date": "2026-11-04",
        "observed_at": CAPTURED,
    }
    result = detect_overlap(
        {"source_version_ids": [], "first_public_at": f"2026-11-{day}T18:00:00Z"},
        anchor,
        set(),
        0.5,
    )
    assert result["overlap_status"] == status


def test_browser_evidence_in_snapshot_replay_needs_no_original(engine, tmp_path, monkeypatch):
    path = bundle(tmp_path)
    with Session(engine) as session, session.begin():
        ingest_capture(session, path, now="2026-11-06T20:01:00Z")
    result = forecast_once(
        "2026-11-06T20:02:00Z", "LIVE", engine=engine, output_dir=tmp_path / "snapshots"
    )
    assert result.status == "COMPLETED"
    manifest, docs = read_snapshot(Path(result.snapshot_path))
    assert docs["npm_capture.json"]["http_status"] is None
    assert docs["npm_page.jpg"] == (path.parent / "page.jpg").read_bytes()
    assert manifest["synthetic"] is False  # isolated test of the production ingestion contract

    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(httpx.Client, "request", forbidden)
    path.rename(path.with_suffix(".unavailable"))
    assert replay_run(result.run_id, engine=engine).result == result.result
