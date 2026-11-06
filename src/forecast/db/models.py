"""Append-only research ledger. Decimal monetary values are stored as canonical text."""

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"
    source_id: Mapped[str] = mapped_column(String, primary_key=True)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    first_public_at: Mapped[str | None] = mapped_column(String)
    first_seen_at: Mapped[str] = mapped_column(String, nullable=False)
    retrieved_at: Mapped[str] = mapped_column(String, nullable=False)
    access_status: Mapped[str] = mapped_column(String, nullable=False)
    parent_source_id: Mapped[str | None] = mapped_column(String, ForeignKey("sources.source_id"))
    origin_group_id: Mapped[str | None] = mapped_column(String)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SourceVersion(Base):
    __tablename__ = "source_versions"
    version_id: Mapped[str] = mapped_column(String, primary_key=True)
    source_id: Mapped[str] = mapped_column(String, ForeignKey("sources.source_id"), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String, nullable=False)
    captured_at: Mapped[str] = mapped_column(String, nullable=False)
    archive_uri: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    raw_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[str | None] = mapped_column(String)
    content_version_status: Mapped[str] = mapped_column(String, nullable=False)
    archive_capture_at: Mapped[str | None] = mapped_column(String)
    archive_verified: Mapped[bool | None] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class Observation(Base):
    __tablename__ = "observations"
    obs_id: Mapped[str] = mapped_column(String, primary_key=True)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    observed_at: Mapped[str] = mapped_column(String, nullable=False)
    asof_et: Mapped[str] = mapped_column(String, nullable=False)
    effective_date: Mapped[str] = mapped_column(String, nullable=False)
    source_version_id: Mapped[str] = mapped_column(
        String, ForeignKey("source_versions.version_id"), nullable=False
    )
    quality_flag: Mapped[str] = mapped_column(String, nullable=False)
    methodology: Mapped[str] = mapped_column(Text, nullable=False)
    ingestion_method: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, default="NPM", nullable=False)
    observation_status: Mapped[str] = mapped_column(String, nullable=False)
    operator: Mapped[str] = mapped_column(String, nullable=False)
    reviewer: Mapped[str | None] = mapped_column(String)
    indicative: Mapped[bool | None] = mapped_column(Boolean, default=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class FinancialFeature(Base):
    __tablename__ = "financial_features"
    feature_id: Mapped[str] = mapped_column(String, primary_key=True)
    feature_type: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    reference_period: Mapped[str] = mapped_column(String, nullable=False)
    first_public_at: Mapped[str] = mapped_column(String, nullable=False)
    first_seen_at: Mapped[str] = mapped_column(String, nullable=False)
    source_version_id: Mapped[str] = mapped_column(
        String, ForeignKey("source_versions.version_id"), nullable=False
    )
    quality_flag: Mapped[str] = mapped_column(String, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class Event(Base):
    __tablename__ = "events"
    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_cluster_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_at: Mapped[str | None] = mapped_column(String)
    effective_at: Mapped[str | None] = mapped_column(String)
    state_asof: Mapped[str] = mapped_column(String, nullable=False)
    state_recorded_at: Mapped[str] = mapped_column(String, nullable=False)
    entity: Mapped[str] = mapped_column(String, nullable=False)
    valuation_basis: Mapped[str] = mapped_column(String, nullable=False)


class ClaimRecord(Base):
    __tablename__ = "claims"
    claim_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("events.event_id"), nullable=False)
    source_version_id: Mapped[str] = mapped_column(
        String, ForeignKey("source_versions.version_id"), nullable=False
    )
    claim_key: Mapped[str] = mapped_column(String, nullable=False)
    claim_value: Mapped[str | None] = mapped_column(Text)
    claim_unit: Mapped[str | None] = mapped_column(String)
    scope: Mapped[dict] = mapped_column(JSON, nullable=False)
    supporting_span: Mapped[str] = mapped_column(Text, nullable=False)
    extractor_model: Mapped[str] = mapped_column(String, nullable=False)
    extractor_version: Mapped[str] = mapped_column(String, nullable=False)
    verification_status: Mapped[str] = mapped_column(String, nullable=False)
    claim_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class EvidenceRelation(Base):
    __tablename__ = "evidence_relations"
    relation_id: Mapped[str] = mapped_column(String, primary_key=True)
    claim_id_a: Mapped[str] = mapped_column(String, ForeignKey("claims.claim_id"), nullable=False)
    claim_id_b: Mapped[str] = mapped_column(String, ForeignKey("claims.claim_id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class EvidenceCluster(Base):
    __tablename__ = "evidence_clusters"
    cluster_id: Mapped[str] = mapped_column(String, primary_key=True)
    representative_claim_id: Mapped[str] = mapped_column(
        String, ForeignKey("claims.claim_id"), nullable=False
    )
    origin_group_id: Mapped[str | None] = mapped_column(String)
    cluster_status: Mapped[str] = mapped_column(String, nullable=False)
    latest_state_asof: Mapped[str] = mapped_column(String, nullable=False)
    dedup_reason: Mapped[str] = mapped_column(Text, nullable=False)


class CausalHypothesis(Base):
    __tablename__ = "causal_hypotheses"
    hypothesis_id: Mapped[str] = mapped_column(String, primary_key=True)
    dag_version: Mapped[str] = mapped_column(String, nullable=False)
    cause_node: Mapped[str] = mapped_column(String, nullable=False)
    effect_node: Mapped[str] = mapped_column(String, nullable=False)
    assumptions: Mapped[dict] = mapped_column(JSON, nullable=False)
    parameter_source: Mapped[str] = mapped_column(String, nullable=False)
    validation_status: Mapped[str] = mapped_column(String, nullable=False)


class ParameterVersion(Base):
    __tablename__ = "parameter_versions"
    parameter_set_id: Mapped[str] = mapped_column(String, primary_key=True)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    json_sha256: Mapped[str] = mapped_column(String, nullable=False)
    origin_type: Mapped[str] = mapped_column(String, nullable=False)
    fitted_until: Mapped[str | None] = mapped_column(String)
    review_status: Mapped[str] = mapped_column(String, nullable=False)
    config_uri: Mapped[str] = mapped_column(Text, nullable=False)


class PredictionRunRecord(Base):
    __tablename__ = "prediction_runs"
    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, nullable=False)
    as_of_utc: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    model_revision: Mapped[str] = mapped_column(String, nullable=False)
    code_commit: Mapped[str] = mapped_column(String, nullable=False)
    config_sha256: Mapped[str] = mapped_column(String, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    data_quality: Mapped[str] = mapped_column(String, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String)
    snapshot_path: Mapped[str | None] = mapped_column(Text)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class PredictionEvidence(Base):
    __tablename__ = "prediction_evidence"
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("prediction_runs.run_id"), primary_key=True
    )
    cluster_id: Mapped[str] = mapped_column(String, primary_key=True)
    included: Mapped[bool] = mapped_column(Boolean, nullable=False)
    exclusion_reason: Mapped[str | None] = mapped_column(String)
    overlap_status: Mapped[str] = mapped_column(String, nullable=False)
    effect_channel: Mapped[str] = mapped_column(String, nullable=False)
    likelihood_set_id: Mapped[str | None] = mapped_column(String)
    alpha: Mapped[float] = mapped_column(Float, nullable=False)


class PredictionBin(Base):
    __tablename__ = "prediction_bins"
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("prediction_runs.run_id"), primary_key=True
    )
    bin_id: Mapped[str] = mapped_column(String, primary_key=True)
    prior_probability: Mapped[float] = mapped_column(Float, nullable=False)
    posterior_probability: Mapped[float] = mapped_column(Float, nullable=False)
    mc_se: Mapped[float] = mapped_column(Float, nullable=False)
    parameter_q05: Mapped[float | None] = mapped_column(Float)
    parameter_q95: Mapped[float | None] = mapped_column(Float)


class PredictionScenario(Base):
    __tablename__ = "prediction_scenarios"
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("prediction_runs.run_id"), primary_key=True
    )
    scenario_id: Mapped[str] = mapped_column(String, primary_key=True)
    prior_weight: Mapped[float] = mapped_column(Float, nullable=False)
    posterior_weight: Mapped[float] = mapped_column(Float, nullable=False)
    conditional_summary_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class RunArtifact(Base):
    __tablename__ = "run_artifacts"
    artifact_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("prediction_runs.run_id"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Settlement(Base):
    __tablename__ = "settlements"
    settlement_id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str] = mapped_column(String, nullable=False)
    target_date: Mapped[str] = mapped_column(String, nullable=False)
    observed_value: Mapped[str | None] = mapped_column(String)
    source_version_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("source_versions.version_id")
    )
    observed_at: Mapped[str] = mapped_column(String, nullable=False)
    settlement_effective_date: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False)
    bin_id: Mapped[str | None] = mapped_column(String)
    method_note: Mapped[str] = mapped_column(Text, nullable=False)


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"
    score_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String, ForeignKey("prediction_runs.run_id"), nullable=False
    )
    settlement_id: Mapped[str] = mapped_column(
        String, ForeignKey("settlements.settlement_id"), nullable=False
    )
    brier: Mapped[float] = mapped_column(Float, nullable=False)
    log_loss: Mapped[float] = mapped_column(Float, nullable=False)
    rps: Mapped[float] = mapped_column(Float, nullable=False)
    evaluation_version: Mapped[str] = mapped_column(String, nullable=False)


class ProviderHealth(Base):
    __tablename__ = "provider_health"
    health_id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    checked_at: Mapped[str] = mapped_column(String, nullable=False)
    last_success_at: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(String)
    details_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class SearchRecord(Base):
    __tablename__ = "search_records"
    search_id: Mapped[str] = mapped_column(String, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[str] = mapped_column(String, nullable=False)
    response_sha256: Mapped[str] = mapped_column(String, nullable=False)
    results_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False)


class ExtractionRecord(Base):
    __tablename__ = "extraction_records"
    extraction_id: Mapped[str] = mapped_column(String, primary_key=True)
    version_id: Mapped[str] = mapped_column(
        String, ForeignKey("source_versions.version_id"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    response_sha256: Mapped[str] = mapped_column(String, nullable=False)
    usage_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
