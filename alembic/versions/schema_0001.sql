-- Frozen schema for migration 0001. Do not regenerate after release.

CREATE TABLE causal_hypotheses (
	hypothesis_id VARCHAR NOT NULL, 
	dag_version VARCHAR NOT NULL, 
	cause_node VARCHAR NOT NULL, 
	effect_node VARCHAR NOT NULL, 
	assumptions JSON NOT NULL, 
	parameter_source VARCHAR NOT NULL, 
	validation_status VARCHAR NOT NULL, 
	PRIMARY KEY (hypothesis_id)
);

CREATE TABLE events (
	event_id VARCHAR NOT NULL, 
	event_cluster_id VARCHAR NOT NULL, 
	event_type VARCHAR NOT NULL, 
	event_at VARCHAR, 
	effective_at VARCHAR, 
	state_asof VARCHAR NOT NULL, 
	state_recorded_at VARCHAR NOT NULL, 
	entity VARCHAR NOT NULL, 
	valuation_basis VARCHAR NOT NULL, 
	PRIMARY KEY (event_id)
);

CREATE TABLE parameter_versions (
	parameter_set_id VARCHAR NOT NULL, 
	model_version VARCHAR NOT NULL, 
	json_sha256 VARCHAR NOT NULL, 
	origin_type VARCHAR NOT NULL, 
	fitted_until VARCHAR, 
	review_status VARCHAR NOT NULL, 
	config_uri TEXT NOT NULL, 
	PRIMARY KEY (parameter_set_id)
);

CREATE TABLE prediction_runs (
	run_id VARCHAR NOT NULL, 
	task_id VARCHAR NOT NULL, 
	as_of_utc VARCHAR NOT NULL, 
	started_at VARCHAR NOT NULL, 
	completed_at VARCHAR, 
	mode VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	model_revision VARCHAR NOT NULL, 
	code_commit VARCHAR NOT NULL, 
	config_sha256 VARCHAR NOT NULL, 
	seed INTEGER NOT NULL, 
	data_quality VARCHAR NOT NULL, 
	error_code VARCHAR, 
	snapshot_path TEXT, 
	warnings_json JSON NOT NULL, 
	PRIMARY KEY (run_id)
);

CREATE TABLE provider_health (
	health_id VARCHAR NOT NULL, 
	provider VARCHAR NOT NULL, 
	checked_at VARCHAR NOT NULL, 
	last_success_at VARCHAR, 
	status VARCHAR NOT NULL, 
	http_status INTEGER, 
	reason VARCHAR, 
	details_json JSON NOT NULL, 
	PRIMARY KEY (health_id)
);

CREATE TABLE search_records (
	search_id VARCHAR NOT NULL, 
	"query" TEXT NOT NULL, 
	requested_at VARCHAR NOT NULL, 
	response_sha256 VARCHAR NOT NULL, 
	results_json JSON NOT NULL, 
	PRIMARY KEY (search_id)
);

CREATE TABLE sources (
	source_id VARCHAR NOT NULL, 
	canonical_url TEXT NOT NULL, 
	publisher VARCHAR NOT NULL, 
	source_type VARCHAR NOT NULL, 
	first_public_at VARCHAR, 
	first_seen_at VARCHAR NOT NULL, 
	retrieved_at VARCHAR NOT NULL, 
	access_status VARCHAR NOT NULL, 
	parent_source_id VARCHAR, 
	origin_group_id VARCHAR, 
	synthetic BOOLEAN NOT NULL, 
	PRIMARY KEY (source_id), 
	FOREIGN KEY(parent_source_id) REFERENCES sources (source_id)
);

CREATE TABLE prediction_bins (
	run_id VARCHAR NOT NULL, 
	bin_id VARCHAR NOT NULL, 
	prior_probability FLOAT NOT NULL, 
	posterior_probability FLOAT NOT NULL, 
	mc_se FLOAT NOT NULL, 
	parameter_q05 FLOAT, 
	parameter_q95 FLOAT, 
	PRIMARY KEY (run_id, bin_id), 
	FOREIGN KEY(run_id) REFERENCES prediction_runs (run_id)
);

CREATE TABLE prediction_evidence (
	run_id VARCHAR NOT NULL, 
	cluster_id VARCHAR NOT NULL, 
	included BOOLEAN NOT NULL, 
	exclusion_reason VARCHAR, 
	overlap_status VARCHAR NOT NULL, 
	effect_channel VARCHAR NOT NULL, 
	likelihood_set_id VARCHAR, 
	alpha FLOAT NOT NULL, 
	PRIMARY KEY (run_id, cluster_id), 
	FOREIGN KEY(run_id) REFERENCES prediction_runs (run_id)
);

CREATE TABLE prediction_scenarios (
	run_id VARCHAR NOT NULL, 
	scenario_id VARCHAR NOT NULL, 
	prior_weight FLOAT NOT NULL, 
	posterior_weight FLOAT NOT NULL, 
	conditional_summary_json JSON NOT NULL, 
	PRIMARY KEY (run_id, scenario_id), 
	FOREIGN KEY(run_id) REFERENCES prediction_runs (run_id)
);

CREATE TABLE run_artifacts (
	artifact_id VARCHAR NOT NULL, 
	run_id VARCHAR NOT NULL, 
	kind VARCHAR NOT NULL, 
	path TEXT NOT NULL, 
	sha256 VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (artifact_id), 
	FOREIGN KEY(run_id) REFERENCES prediction_runs (run_id)
);

CREATE TABLE source_versions (
	version_id VARCHAR NOT NULL, 
	source_id VARCHAR NOT NULL, 
	content_sha256 VARCHAR NOT NULL, 
	captured_at VARCHAR NOT NULL, 
	archive_uri TEXT, 
	title TEXT NOT NULL, 
	raw_excerpt TEXT NOT NULL, 
	published_at VARCHAR, 
	content_version_status VARCHAR NOT NULL, 
	archive_capture_at VARCHAR, 
	archive_verified BOOLEAN, 
	metadata_json JSON NOT NULL, 
	PRIMARY KEY (version_id), 
	FOREIGN KEY(source_id) REFERENCES sources (source_id)
);

CREATE TABLE claims (
	claim_id VARCHAR NOT NULL, 
	event_id VARCHAR NOT NULL, 
	source_version_id VARCHAR NOT NULL, 
	claim_key VARCHAR NOT NULL, 
	claim_value TEXT, 
	claim_unit VARCHAR, 
	scope JSON NOT NULL, 
	supporting_span TEXT NOT NULL, 
	extractor_model VARCHAR NOT NULL, 
	extractor_version VARCHAR NOT NULL, 
	verification_status VARCHAR NOT NULL, 
	claim_json JSON NOT NULL, 
	PRIMARY KEY (claim_id), 
	FOREIGN KEY(event_id) REFERENCES events (event_id), 
	FOREIGN KEY(source_version_id) REFERENCES source_versions (version_id)
);

CREATE TABLE extraction_records (
	extraction_id VARCHAR NOT NULL, 
	version_id VARCHAR NOT NULL, 
	model_id VARCHAR NOT NULL, 
	prompt_version VARCHAR NOT NULL, 
	response_sha256 VARCHAR NOT NULL, 
	usage_json JSON NOT NULL, 
	status VARCHAR NOT NULL, 
	PRIMARY KEY (extraction_id), 
	FOREIGN KEY(version_id) REFERENCES source_versions (version_id)
);

CREATE TABLE financial_features (
	feature_id VARCHAR NOT NULL, 
	feature_type VARCHAR NOT NULL, 
	value VARCHAR NOT NULL, 
	unit VARCHAR NOT NULL, 
	reference_period VARCHAR NOT NULL, 
	first_public_at VARCHAR NOT NULL, 
	first_seen_at VARCHAR NOT NULL, 
	source_version_id VARCHAR NOT NULL, 
	quality_flag VARCHAR NOT NULL, 
	metadata_json JSON NOT NULL, 
	PRIMARY KEY (feature_id), 
	FOREIGN KEY(source_version_id) REFERENCES source_versions (version_id)
);

CREATE TABLE observations (
	obs_id VARCHAR NOT NULL, 
	metric_name VARCHAR NOT NULL, 
	value VARCHAR NOT NULL, 
	unit VARCHAR NOT NULL, 
	observed_at VARCHAR NOT NULL, 
	asof_et VARCHAR NOT NULL, 
	effective_date VARCHAR NOT NULL, 
	source_version_id VARCHAR NOT NULL, 
	quality_flag VARCHAR NOT NULL, 
	methodology TEXT NOT NULL, 
	ingestion_method VARCHAR NOT NULL, 
	provider VARCHAR NOT NULL, 
	observation_status VARCHAR NOT NULL, 
	operator VARCHAR NOT NULL, 
	reviewer VARCHAR, 
	indicative BOOLEAN, 
	synthetic BOOLEAN NOT NULL, 
	PRIMARY KEY (obs_id), 
	FOREIGN KEY(source_version_id) REFERENCES source_versions (version_id)
);

CREATE TABLE settlements (
	settlement_id VARCHAR NOT NULL, 
	task_id VARCHAR NOT NULL, 
	target_date VARCHAR NOT NULL, 
	observed_value VARCHAR, 
	source_version_id VARCHAR, 
	observed_at VARCHAR NOT NULL, 
	settlement_effective_date VARCHAR, 
	status VARCHAR NOT NULL, 
	bin_id VARCHAR, 
	method_note TEXT NOT NULL, 
	PRIMARY KEY (settlement_id), 
	FOREIGN KEY(source_version_id) REFERENCES source_versions (version_id)
);

CREATE TABLE evaluation_scores (
	score_id VARCHAR NOT NULL, 
	run_id VARCHAR NOT NULL, 
	settlement_id VARCHAR NOT NULL, 
	brier FLOAT NOT NULL, 
	log_loss FLOAT NOT NULL, 
	rps FLOAT NOT NULL, 
	evaluation_version VARCHAR NOT NULL, 
	PRIMARY KEY (score_id), 
	FOREIGN KEY(run_id) REFERENCES prediction_runs (run_id), 
	FOREIGN KEY(settlement_id) REFERENCES settlements (settlement_id)
);

CREATE TABLE evidence_clusters (
	cluster_id VARCHAR NOT NULL, 
	representative_claim_id VARCHAR NOT NULL, 
	origin_group_id VARCHAR, 
	cluster_status VARCHAR NOT NULL, 
	latest_state_asof VARCHAR NOT NULL, 
	dedup_reason TEXT NOT NULL, 
	PRIMARY KEY (cluster_id), 
	FOREIGN KEY(representative_claim_id) REFERENCES claims (claim_id)
);

CREATE TABLE evidence_relations (
	relation_id VARCHAR NOT NULL, 
	claim_id_a VARCHAR NOT NULL, 
	claim_id_b VARCHAR NOT NULL, 
	relation_type VARCHAR NOT NULL, 
	reason TEXT NOT NULL, 
	PRIMARY KEY (relation_id), 
	FOREIGN KEY(claim_id_a) REFERENCES claims (claim_id), 
	FOREIGN KEY(claim_id_b) REFERENCES claims (claim_id)
);

