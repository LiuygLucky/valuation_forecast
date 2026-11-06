from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from forecast.domain.time_policy import ET, utc


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class NpmObservation(StrictModel):
    observed_on: date
    valuation_trillion: Decimal = Field(gt=0)
    captured_at: AwareDatetime
    observed_at: AwareDatetime
    url: str
    artifact_path: str
    operator: str = Field(min_length=1)
    methodology: str = Field(min_length=1)
    review_status: Literal["VERIFIED", "UNVERIFIED"]
    reviewer: str | None = None
    ingestion_method: Literal["manual_csv", "manual_entry", "authorized_export"] = "manual_csv"
    metric_type: Literal["npm_valuation"] = "npm_valuation"
    indicative: bool = True
    synthetic: bool = False
    archive_capture_at: AwareDatetime | None = None
    archive_verified: bool = False

    @model_validator(mode="after")
    def check(self):
        if self.observed_at.astimezone(ET).date() != self.observed_on:
            raise ValueError("observed_on must match observation's New York date")
        if utc(self.observed_at) > utc(self.captured_at):
            raise ValueError("capture cannot precede observation")
        if self.review_status == "VERIFIED" and not self.reviewer:
            raise ValueError("verified import requires reviewer")
        if self.archive_verified and (not self.archive_capture_at or not self.reviewer):
            raise ValueError("verified archive requires original capture timestamp and reviewer")
        if self.archive_capture_at and utc(self.archive_capture_at) > utc(self.captured_at):
            raise ValueError("original archive cannot postdate the submitted capture")
        return self


class Claim(StrictModel):
    source_ids: list[str] = Field(min_length=1)
    entity: Literal["OpenAI"] = "OpenAI"
    claim_type: Literal[
        "financing_valuation_target", "financing_completed", "revenue", "compute_cost"
    ]
    event_cluster_id: str = Field(min_length=1)
    event_status: Literal[
        "rumored", "proposed", "committed", "closed", "cancelled", "expired", "corrected"
    ]
    event_at: AwareDatetime | None = None
    effective_at: AwareDatetime | None = None
    published_at: AwareDatetime
    valuation_basis: Literal[
        "pre_money", "post_money", "secondary_implied", "npm_valuation", "unknown"
    ]
    reported_valuation_trillion: Decimal | None = Field(default=None, gt=0)
    supporting_quote: str = Field(min_length=1)
    quote_location: str = Field(min_length=1)
    supported: bool
    causal_mechanisms: list[str] = Field(min_length=1)
    direction: Literal["up", "down", "uncertain", "unchanged"]
    uncertainty_notes: list[str] = Field(default_factory=list)
    scenario_tags: list[str] = Field(default_factory=list)
    drivers: list[str] = Field(default_factory=list)
    mechanism_path_ids: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    synthetic: bool = False

    @field_validator("supporting_quote")
    @classmethod
    def short_quote(cls, value):
        if len(value.split()) > 25:
            raise ValueError("supporting quote exceeds 25 words")
        return value


class Extraction(StrictModel):
    claims: list[Claim]


class BaselineOutput(StrictModel):
    task_id: str
    as_of_utc: datetime
    anchor_value_trillion: float
    anchor_source_id: str
    samples_trillion: list[float]
    prior_bin_probs: dict[str, float]
    scenario_prior: dict[str, float]
    scenario_params: dict[str, dict]
    parameter_provenance: dict[str, str]
    assumptions: list[str]
    data_quality: str


class PredictionRun(StrictModel):
    run_id: str
    mode: str
    status: str
    as_of_utc: str
    snapshot_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
    result: dict = Field(default_factory=dict)
