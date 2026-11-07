from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from forecast.agent.orchestrator import collect_live
from forecast.agent.prompts import PROMPT_VERSION
from forecast.application.demo import demo_inputs
from forecast.application.input_validation import freeze_task_contract, validate_frozen_inputs
from forecast.application.run_modes import RunMode, parse_mode
from forecast.audit.hashing import object_hash, sha256
from forecast.audit.manifest import code_identity, input_manifest, library_versions
from forecast.audit.snapshot import read_snapshot, write_snapshot
from forecast.causal.dag import mermaid
from forecast.causal.scenario_assessor import map_clusters
from forecast.config import TaskConfig, data_dir, load_config, load_yaml
from forecast.db.models import (
    CausalHypothesis,
    EvidenceCluster,
    EvidenceRelation,
    ParameterVersion,
    PredictionBin,
    PredictionEvidence,
    PredictionRunRecord,
    PredictionScenario,
    RunArtifact,
)
from forecast.db.queries import freeze_inputs
from forecast.db.session import init_db
from forecast.domain.schemas import PredictionRun
from forecast.domain.time_policy import utc
from forecast.ingestion.quality import coverage_matrix
from forecast.ingestion.source_graph import build_clusters
from forecast.model.baseline import compute_baseline
from forecast.model.likelihoods import build_likelihoods
from forecast.model.posterior import compute_posterior, sensitivity
from forecast.providers.npm_browser import read_capture
from forecast.reports.render import render_report


def calculate(inputs, as_of, cfg, priors, likelihood_config, dag, quality, archived=False):
    baseline = compute_baseline(inputs["anchor"], as_of, cfg, priors, quality)
    clusters = build_clusters(inputs["claims"], as_of, archived=archived)
    mapped = map_clusters(clusters, dag)
    evidence = build_likelihoods(mapped, inputs["anchor"], inputs["features"], likelihood_config)
    posterior = compute_posterior(baseline, evidence, cfg.seed)
    sensitivity_results = sensitivity(baseline, evidence, cfg.seed)
    for label, factor in (("prior_sigma_low", 0.75), ("prior_sigma_high", 1.25)):
        alternative = deepcopy(priors)
        for values in alternative["scenarios"].values():
            values["sigma"] = [v * factor for v in values["sigma"]]
        alt_baseline = compute_baseline(inputs["anchor"], as_of, cfg, alternative, quality)
        sensitivity_results[label] = compute_posterior(alt_baseline, evidence, cfg.seed)[
            "bin_probabilities"
        ]
    # Explicit alternative to the conservative absorption rule; still only one channel.
    alt = deepcopy(evidence)
    for row in alt:
        if row["overlap_status"] == "PARTIALLY_OR_POSSIBLY_ABSORBED" and row.get("likelihood"):
            row.update(alpha=likelihood_config["alpha"] * 0.5, effect_channel="scenario_weight")
    sensitivity_results["partial_absorption_alternative"] = compute_posterior(
        baseline, alt, cfg.seed
    )["bin_probabilities"]
    return baseline, evidence, posterior, sensitivity_results


def forecast_once(
    as_of=None, mode="LIVE", *, engine=None, output_dir=None, providers=None, archived_inputs=None
) -> PredictionRun:
    cfg = load_config()
    selected_mode = parse_mode(mode)
    experiment = (
        "SYNTHETIC"
        if selected_mode == RunMode.DEMO
        else "HISTORICAL_ARCHIVED"
        if selected_mode == RunMode.HISTORICAL_ARCHIVED
        else "LIVE_PROSPECTIVE"
        if selected_mode == RunMode.LIVE and as_of is None
        else "RETROSPECTIVE_WEAK"
        if as_of is not None
        else "PROVISIONAL"
    )
    if selected_mode == RunMode.REPLAY:
        raise ValueError("REPLAY requires replay_run(run_id)")
    engine = init_db(engine)
    output_dir = Path(output_dir or data_dir() / "snapshots")
    run_id = str(uuid4())
    start = datetime.now(UTC)
    cutoff = utc(as_of) if as_of is not None else start
    identity = code_identity()
    configs = {
        "task": cfg.model_dump(mode="json"),
        "priors": load_yaml("model_priors.yaml"),
        "likelihoods": load_yaml("evidence_likelihoods.yaml"),
        "dag": load_yaml("causal_graph.yaml"),
        "search": load_yaml("search_queries.yaml"),
    }
    config_hash = object_hash(configs)
    with Session(engine) as session, session.begin():
        session.add(
            PredictionRunRecord(
                run_id=run_id,
                task_id=cfg.task_id,
                as_of_utc=cutoff.isoformat(),
                started_at=start.isoformat(),
                mode=selected_mode.value,
                status="RUNNING",
                model_revision=cfg.model_revision,
                code_commit=identity["git_commit"],
                config_sha256=config_hash,
                seed=cfg.seed,
                data_quality="UNKNOWN",
                warnings_json=[],
            )
        )
    warnings = []
    snapshot_path = None
    try:
        if cutoff > cfg.freeze_utc:
            raise ValueError("PREDICTION_FROZEN")
        collection: dict = {"warnings": [], "search_ids": []}
        if selected_mode == RunMode.DEMO:
            inputs = demo_inputs(cutoff)
            quality = "DEMO"
            warnings.extend(
                ["DEMO/SYNTHETIC: all observations and news are fictional", "UNCALIBRATED"]
            )
        elif selected_mode == RunMode.HISTORICAL_ARCHIVED:
            if archived_inputs is None:
                raise ValueError("ARCHIVE_REQUIRED")
            inputs = deepcopy(archived_inputs)
            if any(s.get("synthetic") for s in inputs["sources"]):
                raise ValueError("SYNTHETIC_NOT_ALLOWED")
            quality = "VERIFIED"
        else:
            if as_of is None:
                collection = collect_live(engine, **(providers or {}))
                cutoff = datetime.now(UTC)
                if cutoff > cfg.freeze_utc:
                    raise ValueError("PREDICTION_FROZEN")
            else:
                # Explicit historical cutoffs use only already-seen data, never contemporary search.
                warnings.append("STORED_AS_OF_ONLY: no present-day web used for an explicit cutoff")
                if cutoff > datetime.now(UTC):
                    raise ValueError("FUTURE_AS_OF_FORBIDDEN")
            warnings.extend(collection["warnings"])
            with Session(engine) as session:
                inputs = freeze_inputs(
                    session, cutoff, provisional=selected_mode == RunMode.PROVISIONAL
                )
            quality = "VERIFIED" if selected_mode == RunMode.LIVE else "PROVISIONAL"
        validate_frozen_inputs(inputs, cutoff, selected_mode.value)
        if selected_mode == RunMode.LIVE:
            freeze_task_contract(output_dir.parent, configs["task"])
        baseline, evidence, posterior, sensitivities = calculate(
            inputs,
            cutoff,
            cfg,
            configs["priors"],
            configs["likelihoods"],
            configs["dag"],
            quality,
            archived=selected_mode == RunMode.HISTORICAL_ARCHIVED,
        )
        if not any(e["included"] for e in evidence):
            warnings.append("BASELINE_ONLY: no eligible unabsorbed evidence likelihood")
        if quality == "PROVISIONAL":
            warnings.append("USER_PROVIDED_UNVERIFIED: provisional anchor; not a verified forecast")
        warnings.extend(
            [
                "UNCALIBRATED: expert_heuristic parameters",
                "NPM schedule is a page claim, not a guarantee; date-only quotes have no precise update timestamp",
            ]
        )
        coverage = coverage_matrix(inputs, cutoff)
        report = render_report(
            run_id,
            selected_mode.value,
            cutoff.isoformat(),
            inputs,
            baseline,
            posterior,
            evidence,
            sensitivities,
            warnings,
        )
        documents = {
            "inputs.json": inputs,
            "configs.json": configs,
            "baseline.json": baseline,
            "evidence.json": evidence,
            "overlap.json": [
                {
                    k: e.get(k)
                    for k in (
                        "cluster_id",
                        "overlap_status",
                        "alpha",
                        "effect_channel",
                        "exclusion_reason",
                    )
                }
                for e in evidence
            ],
            "posterior.json": posterior,
            "sensitivity.json": sensitivities,
            "coverage.json": coverage,
            "report.md": report,
            "causal_graph.mmd": mermaid(configs["dag"]),
        }
        # Embed anchor provenance inside this immutable run; replay must not depend on live files.
        for source in inputs["sources"]:
            if source["version_id"] != inputs["anchor"]["source_version_id"]:
                continue
            if source.get("metadata_json", {}).get("capture_method") == "public_browser":
                capture_path = Path(source["archive_uri"])
                record, _ = read_capture(capture_path)
                documents["npm_capture.json"] = record
                for filename in record["artifacts"]:
                    documents["npm_" + filename] = (capture_path.parent / filename).read_bytes()
        documents["collection.json"] = collection
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": cfg.task_id,
            "as_of_utc": cutoff.isoformat(),
            "mode": selected_mode.value,
            "experiment": experiment,
            "synthetic": quality == "DEMO",
            "data_quality": quality,
            "model_revision": cfg.model_revision,
            "seed": cfg.seed,
            "code": identity,
            "libraries": library_versions(),
            "config_sha256": config_hash,
            "parameter_sha256": {k: object_hash(v) for k, v in configs.items()},
            "input_records": input_manifest(inputs),
            "search_ids": collection["search_ids"],
            "llm": {
                "prompt_version": PROMPT_VERSION,
                "input_prompt_versions": sorted(
                    {c["extractor_version"] for c in inputs["claims"] if c.get("extractor_version")}
                ),
                "models": sorted({c.get("extractor_model", "synthetic") for c in inputs["claims"]}),
            },
            "result_sha256": object_hash(posterior),
            "warnings": warnings,
            "status": "COMPUTED; completed run status is committed in SQLite",
        }
        snapshot_path, hashes = write_snapshot(output_dir, run_id, documents, manifest)
        now = datetime.now(UTC).isoformat()
        with Session(engine) as session, session.begin():
            parameter_id = "params_" + config_hash
            if not session.get(ParameterVersion, parameter_id):
                session.add(
                    ParameterVersion(
                        parameter_set_id=parameter_id,
                        model_version=cfg.model_revision,
                        json_sha256=config_hash,
                        origin_type="expert_heuristic",
                        review_status="UNCALIBRATED",
                        config_uri=str(snapshot_path / "configs.json"),
                    )
                )
            for edge in configs["dag"]["edges"]:
                hid = configs["dag"]["version"] + ":" + edge["id"]
                if not session.get(CausalHypothesis, hid):
                    session.add(
                        CausalHypothesis(
                            hypothesis_id=hid,
                            dag_version=configs["dag"]["version"],
                            cause_node=edge["cause"],
                            effect_node=edge["effect"],
                            assumptions=edge,
                            parameter_source=edge["parameter_source"],
                            validation_status="NOT_IDENTIFIED",
                        )
                    )
            for row in evidence:
                session.add(
                    PredictionEvidence(
                        run_id=run_id,
                        cluster_id=row["cluster_id"],
                        included=row["included"],
                        exclusion_reason=row.get("exclusion_reason"),
                        overlap_status=row["overlap_status"],
                        effect_channel=row["effect_channel"],
                        likelihood_set_id=parameter_id,
                        alpha=row["alpha"],
                    )
                )
                if selected_mode != RunMode.DEMO and row.get("representative_claim_id"):
                    if not session.get(EvidenceCluster, row["cluster_id"]):
                        session.add(
                            EvidenceCluster(
                                cluster_id=row["cluster_id"],
                                representative_claim_id=row["representative_claim_id"],
                                origin_group_id=row["sources"][0].get("origin_group_id"),
                                cluster_status=row.get("exclusion_reason") or "VERIFIED",
                                latest_state_asof=row["first_public_at"],
                                dedup_reason=row["dedup_reason"],
                            )
                        )
                    for cid in row["claim_ids"]:
                        if cid != row["representative_claim_id"]:
                            rid = object_hash([cid, row["representative_claim_id"]])
                            if not session.get(EvidenceRelation, rid):
                                session.add(
                                    EvidenceRelation(
                                        relation_id=rid,
                                        claim_id_a=cid,
                                        claim_id_b=row["representative_claim_id"],
                                        relation_type="derived_from",
                                        reason="Conservative shared event/origin clustering, not proven citation",
                                    )
                                )
            for k, p in posterior["bin_probabilities"].items():
                session.add(
                    PredictionBin(
                        run_id=run_id,
                        bin_id=k,
                        prior_probability=baseline["prior_bin_probs"][k],
                        posterior_probability=p,
                        mc_se=posterior["mc_se"][k],
                    )
                )
            for s, w in posterior["scenario_posterior"].items():
                session.add(
                    PredictionScenario(
                        run_id=run_id,
                        scenario_id=s,
                        prior_weight=baseline["scenario_prior"][s],
                        posterior_weight=w,
                        conditional_summary_json=baseline["conditional_summaries"][s],
                    )
                )
            for name, digest in hashes.items():
                session.add(
                    RunArtifact(
                        artifact_id=str(uuid4()),
                        run_id=run_id,
                        kind=name,
                        path=str(snapshot_path / name),
                        sha256=digest,
                        created_at=now,
                    )
                )
            run = session.get(PredictionRunRecord, run_id)
            assert run is not None
            run.status, run.completed_at, run.data_quality = "COMPLETED", now, quality
            run.as_of_utc, run.snapshot_path, run.warnings_json = (
                cutoff.isoformat(),
                str(snapshot_path),
                warnings,
            )
        return PredictionRun(
            run_id=run_id,
            mode=selected_mode.value,
            status="COMPLETED",
            as_of_utc=cutoff.isoformat(),
            snapshot_path=str(snapshot_path),
            warnings=warnings,
            result={k: v for k, v in posterior.items() if k != "posterior_samples"},
        )
    except Exception as error:
        allowed = {
            "NO_VALID_ANCHOR",
            "PREDICTION_FROZEN",
            "ARCHIVE_REQUIRED",
            "SYNTHETIC_NOT_ALLOWED",
            "FUTURE_AS_OF_FORBIDDEN",
            "ANCHOR_TIME_LEAKAGE",
            "DEMO_REQUIRES_SYNTHETIC_INPUTS",
            "ANCHOR_SOURCE_INVALID",
            "ANCHOR_METRIC_MISMATCH",
            "FEATURE_TIME_LEAKAGE",
            "CLAIM_SOURCE_MISMATCH",
            "INPUT_SOURCE_INVALID",
            "ARCHIVE_PROOF_REQUIRED",
            "ARCHIVE_HASH_MISMATCH",
            "FROZEN_TASK_CONFIG_CHANGED",
        }
        code = str(error) if str(error) in allowed else "PIPELINE_ERROR:" + type(error).__name__
        with Session(engine) as session, session.begin():
            run = session.get(PredictionRunRecord, run_id)
            assert run is not None
            run.status, run.error_code = "FAILED", code
            run.completed_at = datetime.now(UTC).isoformat()
            run.warnings_json = warnings + [code]
            run.snapshot_path = str(snapshot_path) if snapshot_path else None
        return PredictionRun(
            run_id=run_id,
            mode=selected_mode.value,
            status=code,
            as_of_utc=cutoff.isoformat(),
            warnings=warnings + [code],
        )


def replay_run(run_id, *, engine=None) -> PredictionRun:
    UUID(run_id)
    engine = init_db(engine)
    with Session(engine) as session:
        run = session.get(PredictionRunRecord, run_id)
        if not run or run.status != "COMPLETED" or run.snapshot_path is None:
            raise ValueError("completed run not found")
        path = Path(run.snapshot_path)
        manifest_index = session.scalar(
            select(RunArtifact).where(
                RunArtifact.run_id == run_id, RunArtifact.kind == "manifest.json"
            )
        )
        if (
            manifest_index is None
            or sha256((path / "manifest.json").read_bytes()) != manifest_index.sha256
        ):
            raise ValueError("MANIFEST_HASH_MISMATCH")
    manifest, docs = read_snapshot(path)
    if manifest["code"]["source_sha256"] != code_identity()["source_sha256"]:
        raise ValueError("CODE_VERSION_MISMATCH: restore the recorded source version")
    if manifest["libraries"] != library_versions():
        raise ValueError("DEPENDENCY_VERSION_MISMATCH: restore locked environment")
    configs = docs["configs.json"]
    _, _, posterior, _ = calculate(
        docs["inputs.json"],
        manifest["as_of_utc"],
        TaskConfig.model_validate(configs["task"]),
        configs["priors"],
        configs["likelihoods"],
        configs["dag"],
        manifest["data_quality"],
        archived=manifest["mode"] == "HISTORICAL_ARCHIVED",
    )
    if not np.allclose(
        list(posterior["bin_probabilities"].values()),
        list(docs["posterior.json"]["bin_probabilities"].values()),
        rtol=0,
        atol=1e-12,
    ):
        raise ValueError("REPLAY_NUMERICAL_MISMATCH")
    if object_hash(posterior) != manifest["result_sha256"]:
        raise ValueError("REPLAY_RESULT_HASH_MISMATCH")
    return PredictionRun(
        run_id=run_id,
        mode="REPLAY",
        status="REPRODUCED",
        as_of_utc=manifest["as_of_utc"],
        snapshot_path=str(path),
        warnings=["Offline replay; not a new prospective forecast"],
        result={k: v for k, v in posterior.items() if k != "posterior_samples"},
    )
