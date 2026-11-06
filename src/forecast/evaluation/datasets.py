import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from forecast.audit.hashing import object_hash, sha256
from forecast.domain.schemas import StrictModel
from forecast.domain.time_policy import availability_reason, local_time, utc


class AuxiliaryTask(StrictModel):
    task_id: str
    company: str
    metric: str
    source_family: str
    experiment: Literal["HISTORICAL_ARCHIVED", "RETROSPECTIVE_WEAK", "SYNTHETIC"]
    as_of: AwareDatetime
    target_date: date
    settlement_value: str
    settlement_effective_date: date
    settlement_archive_uri: str
    settlement_sha256: str
    event_families: list[str]
    inputs: dict
    seed: int = 20261107
    monte_carlo_samples: int = Field(default=20000, ge=100)
    parameter_fitted_until: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if utc(self.as_of) >= local_time(self.target_date):
            raise ValueError("forecast origin must precede target")
        if self.settlement_effective_date > self.target_date:
            raise ValueError("settlement cannot be after target")
        if self.parameter_fitted_until and utc(self.parameter_fitted_until) >= utc(self.as_of):
            raise ValueError("parameters fitted on future data")
        return self


def load_dataset(path: Path):
    if not path.is_file():
        raise ValueError("DATA_UNAVAILABLE: no archived dataset supplied")
    raw = json.loads(path.read_text(encoding="utf-8"))
    tasks = [AuxiliaryTask.model_validate(item) for item in raw["tasks"]]
    if not tasks:
        raise ValueError("DATA_UNAVAILABLE: empty dataset")
    if len({t.task_id for t in tasks}) != len(tasks):
        raise ValueError("duplicate task IDs")
    return tasks


def validate_archive(task: AuxiliaryTask):
    anchor = task.inputs.get("anchor")
    if not anchor or utc(anchor["observed_at"]) > utc(task.as_of):
        raise ValueError("ANCHOR_TIME_LEAKAGE_OR_MISSING")
    if task.experiment != "SYNTHETIC":
        sources_by_id = {s["version_id"]: s for s in task.inputs["sources"]}
        source = sources_by_id.get(anchor["source_version_id"])
        if not source or anchor.get("synthetic") or anchor["metric_name"] != task.metric:
            raise ValueError("ANCHOR_SOURCE_OR_METRIC_INVALID")
        if availability_reason(source, task.as_of, task.experiment == "HISTORICAL_ARCHIVED"):
            raise ValueError("ANCHOR_TIME_LEAKAGE")
        for claim in task.inputs["claims"]:
            source = claim["source"]
            if source["version_id"] not in sources_by_id or object_hash(source) != object_hash(
                sources_by_id[source["version_id"]]
            ):
                raise ValueError("CLAIM_SOURCE_MISMATCH")
    if task.experiment != "HISTORICAL_ARCHIVED":
        return
    sources = task.inputs["sources"]
    for source in sources:
        if source.get("synthetic") or not source.get("archive_verified"):
            raise ValueError("ARCHIVE_PROOF_REQUIRED")
        if availability_reason(source, task.as_of, archived=True):
            raise ValueError("ARCHIVE_TIME_LEAKAGE")
        path = Path(source.get("archive_uri", ""))
        digest = source.get("metadata_json", {}).get("artifact_sha256")
        if not path.is_file() or not digest or sha256(path.read_bytes()) != digest:
            raise ValueError("ARCHIVE_HASH_MISMATCH")
    if task.inputs["anchor"].get("quality_flag") != "VERIFIED":
        raise ValueError("NO_VALID_ANCHOR")
    if utc(task.inputs["anchor"]["observed_at"]) > utc(task.as_of):
        raise ValueError("ANCHOR_TIME_LEAKAGE")
    path = Path(task.settlement_archive_uri)
    if not path.is_file() or sha256(path.read_bytes()) != task.settlement_sha256:
        raise ValueError("SETTLEMENT_ARCHIVE_HASH_MISMATCH")


def purged_rolling_origin(tasks, test_index, purge_days=7):
    ordered = sorted(tasks, key=lambda t: utc(t.as_of))
    test = ordered[test_index]
    training = [
        t
        for t in ordered[:test_index]
        if (utc(test.as_of) - local_time(t.target_date)).days >= purge_days
        and not set(t.event_families) & set(test.event_families)
    ]
    return training, test
