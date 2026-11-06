from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import numpy as np

from forecast.audit.hashing import object_hash, stable_json
from forecast.domain.bins import classify
from forecast.evaluation.ablation import ablation_predictions
from forecast.evaluation.datasets import load_dataset, purged_rolling_origin, validate_archive
from forecast.evaluation.metrics import calibration, score


def run_backtest(dataset_path: Path, output_dir: Path):
    tasks = load_dataset(dataset_path)
    records, failures = [], []
    ordered = sorted(tasks, key=lambda t: t.as_of)
    for index in range(len(ordered)):
        training, task = purged_rolling_origin(ordered, index)
        started = perf_counter()
        try:
            validate_archive(task)
            predictions = ablation_predictions(task)
            observed_bin = classify(task.settlement_value)
            for model, result in predictions.items():
                records.append(
                    {
                        "task_id": task.task_id,
                        "model": model,
                        "experiment": task.experiment,
                        "source_family": task.source_family,
                        "metric": task.metric,
                        "as_of": task.as_of.isoformat(),
                        "observed_bin": observed_bin,
                        **result,
                        **score(result["probabilities"], observed_bin),
                        "purged_training_ids": [t.task_id for t in training],
                        "parameter_status": "heuristic; no fitting performed",
                        "api_cost_usd": 0,
                        "elapsed_seconds_all_variants": perf_counter() - started,
                    }
                )
        except (ValueError, KeyError, TypeError) as error:
            failures.append({"task_id": task.task_id, "status": str(error)})
    groups = defaultdict(list)
    for row in records:
        groups[(row["experiment"], row["source_family"], row["metric"], row["model"])].append(row)
    aggregates = [
        {
            "experiment": key[0],
            "source_family": key[1],
            "metric": key[2],
            "model": key[3],
            "n": len(rows),
            **{
                metric: float(np.mean([r[metric] for r in rows]))
                for metric in ("brier", "log_loss", "rps")
            },
            "calibration": calibration(rows),
        }
        for key, rows in groups.items()
    ]
    report = {
        "dataset_sha256": object_hash([t.model_dump(mode="json") for t in tasks]),
        "created_at": datetime.now(UTC).isoformat(),
        "records": records,
        "failures": failures,
        "aggregates": aggregates,
        "log_loss_epsilon": 1e-12,
        "limitation": "M5 calibration is NOT_FITTED; no claimed accuracy improvement",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / ("backtest_" + str(uuid4()) + ".json")
    with path.open("x", encoding="utf-8") as f:
        f.write(stable_json(report))
    return {
        "output": str(path),
        "tasks": len(tasks),
        "scored_records": len(records),
        "failures": failures,
    }
