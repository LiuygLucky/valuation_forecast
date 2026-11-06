from datetime import date, datetime
from decimal import Decimal

import numpy as np
import pytest

from forecast.config import TaskConfig, load_config
from forecast.domain.bins import bin_probs, classify, validate_probabilities
from forecast.domain.schemas import Claim, NpmObservation
from forecast.domain.time_policy import ET, availability_reason, local_time, utc
from forecast.domain.units import Money


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0.849999", "B1"),
        ("0.85", "B2"),
        ("1.00", "B3"),
        ("1.15", "B4"),
        ("1.30", "B5"),
        ("1.45", "B5"),
        ("1.450001", "B6"),
    ],
)
def test_exact_boundaries(value, expected):
    assert classify(Decimal(value)) == expected
    assert bin_probs(np.array([float(value)]))[expected] == 1


@pytest.mark.parametrize("value", [0, -1, "NaN", "Infinity"])
def test_invalid_valuation(value):
    with pytest.raises(ValueError):
        classify(value)


def test_config_frozen_contract():
    cfg = load_config()
    assert cfg.freeze_utc.isoformat() == "2026-12-31T17:59:59+00:00"
    data = cfg.model_dump(mode="json")
    for key, value in [
        ("settlement_target_date", "2027-01-01"),
        ("prediction_freeze_local", "2026-12-31T13:00:00"),
        ("intervals", []),
    ]:
        with pytest.raises(ValueError):
            TaskConfig.model_validate(data | {key: value})
    data["intervals"][4]["upper_closed"] = False
    with pytest.raises(ValueError):
        TaskConfig.model_validate(data)


def test_timezone_dst_and_naive():
    assert local_time(date(2026, 7, 1)).hour == 17
    assert local_time(date(2026, 12, 1)).hour == 18
    with pytest.raises(ValueError):
        utc(datetime(2026, 1, 1))
    assert utc("2026-07-01T13:00:00-04:00").astimezone(ET).hour == 13


def test_information_not_event_time_and_revisions():
    source = {
        "event_at": "2026-10-20T00:00:00Z",
        "first_public_at": "2026-10-25T00:00:00Z",
        "first_seen_at": "2026-10-25T01:00:00Z",
    }
    assert availability_reason(source, utc("2026-10-22T00:00:00Z")) == "EXCLUDED_FUTURE"
    assert availability_reason(source, utc("2026-10-26T00:00:00Z")) is None
    assert (
        availability_reason(
            source | {"captured_at": "2026-11-01T00:00:00Z"}, utc("2026-10-26T00:00:00Z")
        )
        == "EXCLUDED_FUTURE"
    )
    assert availability_reason({}, utc("2026-10-26T00:00:00Z")) == "QUARANTINED_TIME_UNKNOWN"
    assert (
        availability_reason(
            {"published_at": source["first_public_at"]}, utc("2026-10-26T00:00:00Z")
        )
        == "QUARANTINED_TIME_UNKNOWN"
    )
    archive = source | {
        "first_seen_at": "2026-11-01T00:00:00Z",
        "archive_capture_at": "2026-10-25T02:00:00Z",
        "archive_verified": True,
    }
    assert availability_reason(archive, utc("2026-10-26T00:00:00Z"), True) is None


def test_probability_errors():
    for values in (
        {"B1": 1},
        dict.fromkeys([f"B{i}" for i in range(1, 7)], 0.1),
        {f"B{i}": (float("nan") if i == 1 else 0.2) for i in range(1, 7)},
    ):
        with pytest.raises(ValueError):
            validate_probabilities(values)
    for samples in ([], [0], [-1], [float("inf")]):
        with pytest.raises(ValueError):
            bin_probs(np.array(samples))


def test_currency_and_metric_contract():
    assert Money(amount_raw="2", currency="USD", scale="1000").amount_usd == 2000
    assert Money(amount_raw="2", currency="EUR", scale=1).amount_usd is None
    assert Money(
        amount_raw=2, currency="EUR", scale=1, fx_rate="1.1", fx_rate_source_id="src"
    ).amount_usd == Decimal("2.2")
    with pytest.raises(ValueError):
        Money(amount_raw=2, currency="EUR", scale=1, amount_usd=3)
    with pytest.raises(ValueError):
        Money(amount_raw=2, currency="USD", scale=1, amount_usd=3)


def test_manual_observation_schema():
    data = dict(
        observed_on="2026-11-06",
        valuation_trillion="1.2",
        captured_at="2026-11-06T18:05:00Z",
        observed_at="2026-11-06T18:00:00Z",
        url=load_config().metric_url,
        artifact_path="capture.png",
        operator="test",
        methodology="indicative",
        review_status="VERIFIED",
        reviewer="reviewer",
    )
    assert NpmObservation(**data).indicative
    for override in (
        {"observed_on": "2026-11-07"},
        {"reviewer": None},
        {"captured_at": "2026-11-06T17:00:00Z"},
    ):
        with pytest.raises(ValueError):
            NpmObservation(**(data | override))


def test_claim_cannot_accept_probability():
    with pytest.raises(ValueError):
        Claim.model_validate({"delta_probability": 0.1})
