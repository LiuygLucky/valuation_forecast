import argparse
import json
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from forecast.application.pipeline import forecast_once, replay_run
from forecast.application.settlement import settle
from forecast.config import ROOT, data_dir
from forecast.db.models import PredictionRunRecord
from forecast.db.session import init_db
from forecast.evaluation.backtest import run_backtest
from forecast.providers.npm_manual import import_csv


def main(argv=None):
    load_dotenv(ROOT / ".env", override=False)
    parser = argparse.ArgumentParser(
        description="Fixed OpenAI 2026-12-31 NPM valuation research tool"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db")
    imp = commands.add_parser("import-npm")
    imp.add_argument("--csv", type=Path, required=True)
    predict = commands.add_parser("forecast")
    predict.add_argument("--mode", choices=["demo", "live", "provisional"], default="live")
    predict.add_argument("--as-of")
    replay = commands.add_parser("replay")
    replay.add_argument("--run-id", required=True)
    backtest = commands.add_parser("backtest")
    backtest.add_argument("--dataset", required=True, type=Path)
    ablation = commands.add_parser("ablation")
    ablation.add_argument("--dataset", required=True, type=Path)
    settlement = commands.add_parser("settle")
    settlement.add_argument("--target-date", default="2026-12-31")
    settlement.add_argument("--valuation")
    settlement.add_argument("--source-id")
    settlement.add_argument("--confirm-final-observation", action="store_true")
    settlement.add_argument("--method-note", default="")
    commands.add_parser("list-runs")
    commands.add_parser("recover")
    args = parser.parse_args(argv)
    result: dict | list
    try:
        if args.command == "init-db":
            init_db()
            result = {"status": "INITIALIZED"}
        elif args.command == "import-npm":
            with Session(init_db()) as session, session.begin():
                result = {"imported": import_csv(session, args.csv, data_dir() / "raw")}
        elif args.command == "forecast":
            result = forecast_once(args.as_of, args.mode).model_dump(mode="json")
        elif args.command == "replay":
            result = replay_run(args.run_id).model_dump(mode="json")
        elif args.command in ("backtest", "ablation"):
            result = run_backtest(args.dataset, data_dir() / "outputs")
        elif args.command == "settle":
            result = settle(
                valuation=args.valuation,
                source_id=args.source_id,
                target_date=args.target_date,
                confirm_final_observation=args.confirm_final_observation,
                method_note=args.method_note,
            )
        elif args.command == "recover":
            from datetime import UTC, datetime, timedelta

            cutoff = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
            with Session(init_db()) as session, session.begin():
                stale = session.scalars(
                    select(PredictionRunRecord).where(
                        PredictionRunRecord.status == "RUNNING",
                        PredictionRunRecord.started_at < cutoff,
                    )
                ).all()
                for run in stale:
                    run.status, run.error_code = "FAILED", "INTERRUPTED_PROCESS"
                    run.completed_at = datetime.now(UTC).isoformat()
                result = {"marked_interrupted": [r.run_id for r in stale]}
        else:
            with Session(init_db()) as session:
                result = [
                    {
                        "run_id": r.run_id,
                        "mode": r.mode,
                        "status": r.status,
                        "as_of": r.as_of_utc,
                        "snapshot": r.snapshot_path,
                    }
                    for r in session.scalars(
                        select(PredictionRunRecord).order_by(PredictionRunRecord.started_at.desc())
                    )
                ]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if isinstance(result, dict) and result.get("status") in (
            "NO_VALID_ANCHOR",
            "PREDICTION_FROZEN",
            "FUTURE_AS_OF_FORBIDDEN",
        ):
            return 2
        if isinstance(result, dict) and str(result.get("status", "")).startswith("PIPELINE_ERROR"):
            return 2
        return 0
    except (ValueError, FileNotFoundError) as error:
        from forecast.audit.hashing import redact

        print(json.dumps({"status": "ERROR", "reason": redact(str(error))}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
