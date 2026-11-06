import math

import pytest

from forecast.domain.bins import BIN_IDS
from forecast.evaluation.datasets import AuxiliaryTask, purged_rolling_origin, validate_archive
from forecast.evaluation.metrics import calibration, score


def test_scores_known_examples():
    perfect = dict.fromkeys(BIN_IDS, 0.0) | {"B5": 1.0}
    assert score(perfect, "B5") == {"brier": 0.0, "log_loss": -0.0, "rps": 0.0}
    wrong = dict.fromkeys(BIN_IDS, 0.0) | {"B1": 1.0}
    assert score(wrong, "B6") == {"brier": 2.0, "log_loss": -math.log(1e-12), "rps": 5.0}
    uniform = dict.fromkeys(BIN_IDS, 1 / 6)
    assert score(uniform, "B1")["brier"] == pytest.approx(5 / 6)
    assert calibration([{"probabilities": uniform, "observed_bin": "B1"}])["ece"] is None
    calibrated = calibration([{"probabilities": perfect, "observed_bin": "B5"}] * 100)
    assert calibrated["ece"] == 0 and sum(b["n"] for b in calibrated["buckets"]) == 100


def test_archived_guard_and_purged_rolling(demo):
    common = dict(
        company="Test Company",
        metric="npm_valuation",
        source_family="NPM",
        experiment="SYNTHETIC",
        target_date="2026-12-31",
        settlement_value="1.45",
        settlement_effective_date="2026-12-31",
        settlement_archive_uri="",
        settlement_sha256="",
        event_families=["shared"],
        inputs=demo,
    )
    task = AuxiliaryTask(task_id="test", as_of="2026-11-07T17:00:00Z", **common)
    validate_archive(task)
    with pytest.raises(ValueError, match="ARCHIVE|ANCHOR"):
        validate_archive(task.model_copy(update={"experiment": "HISTORICAL_ARCHIVED"}))
    earlier = task.model_copy(update={"task_id": "earlier"})
    train, _ = purged_rolling_origin([earlier, task], 1)
    assert train == []
    with pytest.raises(ValueError):
        AuxiliaryTask(task_id="bad", as_of="2027-01-01T00:00:00Z", **common)
