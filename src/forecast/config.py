import os
from datetime import date, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, model_validator

from forecast.domain.schemas import StrictModel
from forecast.domain.time_policy import ET, utc

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"


class Interval(StrictModel):
    id: str
    label: str
    lower: float | None
    upper: float | None
    lower_closed: bool
    upper_closed: bool


class TaskConfig(StrictModel):
    task_id: Literal["openai_npm_valuation_20261231"]
    question: str
    company: Literal["OpenAI"]
    metric: Literal["npm_valuation"]
    metric_url: Literal[
        "https://fe.secondmarket.com/companies/company-30839e0b-2730-4495-839f-1bf638fa9cca/data"
    ]
    currency: Literal["USD"]
    internal_unit: Literal["USD_trillion"]
    business_timezone: Literal["America/New_York"]
    prediction_freeze_local: str
    settlement_target_date: date
    source_update_time_local_claimed: Literal["13:00"]
    intervals: list[Interval]
    seed: int = Field(ge=0)
    monte_carlo_samples: int = Field(ge=100)
    model_revision: str

    @model_validator(mode="after")
    def contract(self):
        edges = [None, 0.85, 1.0, 1.15, 1.30, 1.45, None]
        if len(self.intervals) != 6:
            raise ValueError("fixed six bins required")
        for i, b in enumerate(self.intervals):
            expected = (f"B{i + 1}", edges[i], edges[i + 1], 0 < i < 5, i == 4)
            if (b.id, b.lower, b.upper, b.lower_closed, b.upper_closed) != expected:
                raise ValueError("fixed settlement interval contract changed")
        if self.settlement_target_date != date(2026, 12, 31):
            raise ValueError("fixed target date")
        if self.prediction_freeze_local != "2026-12-31T12:59:59":
            raise ValueError("fixed freeze time")
        return self

    @property
    def freeze_utc(self):
        return utc(datetime.fromisoformat(self.prediction_freeze_local).replace(tzinfo=ET))


def load_yaml(name: str) -> dict:
    return yaml.safe_load((CONFIG_DIR / name).read_text(encoding="utf-8"))


def load_config() -> TaskConfig:
    return TaskConfig.model_validate(load_yaml("task_config.yaml"))


def data_dir() -> Path:
    return Path(os.getenv("FORECAST_DATA_DIR", str(ROOT / "data"))).resolve()
