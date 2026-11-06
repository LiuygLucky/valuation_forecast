# Work log

## Iteration 0 — 2026-11-07
- Inspected Prompt_V1.md and empty project structure; no applicable AGENTS.md found.
- Created implementation checklist and persistent resume instructions.
- Next: create package/environment and implement strict config/domain contracts, then database.
- Tests: not yet run. Data: no verified real observations; calibration: none.

## Iteration 1 — domain / ledger / deterministic engine
- Added package/environment/uv.lock, frozen configs, domain/time/unit contracts, SQLite/Alembic, NPM import.
- Added Student-t scenario simulation, log likelihood update, overlap and sensitivity.
- Domain tests: 18 passed. Restricted proxy install failed first; authorized installation succeeded.

## Iteration 2 — evidence / providers / audit / UI
- Added extractor/verifier/state/source graph, DAG, mockable providers and budgeted collection.
- Added snapshots/report/service/CLI/Streamlit/settlement/evaluation/M0–M5.
- Initial full suite: 52 passed,1 dashboard test path failure. Fixed absolute AppTest path and ORM typing.
- Follow-up:53 passed; mypy clean; Dashboard button exercised via AppTest.
- Real smoke: Tavily200,DeepSeek401; credentials not printed, safe results in docs/api_smoke.json.

## Iteration 3 — audit review / regressions / documentation
- Fixed historical import first_seen_at to actual ingestion time; archive proof remains separate.
- Fixed delayed reprints evading absorption; earliest identical fact retained in latest state.
- Bound monetary amounts to valuation phrase, preventing financing amount substitution.
- Froze migration SQL; added source/hash checks, task freeze, conservative event-family identity.
- Added README, ADR, assumptions/methodology/API/source docs, CSV template and launcher.
- Latest completed suite:56 passed;391 core statements/3 uncovered=99.23%.
- Synthetic backtest:2 tasks/12 model records/0 failures. archived_v1 missing → DATA_UNAVAILABLE, expected.
- Next: final regression, CLI/REPLAY, final report and file manifest.
- Data authenticity: no real NPM observation supplied; fixtures fictional; calibration:none.
