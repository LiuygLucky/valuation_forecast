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

## Final delivery — 2026-11-07
- Final regression:58 passed,0 failed; core coverage99.23%;ruff/mypy/dependency check passed.
- Added certified historical archive mode and frozen-contract tests.
- Local Git initialized:2c20111 implementation;af956d1 pins LF line endings. Credentials/prompt/data excluded.
- Final DEMO:ff3de36d-8e8d-4a4b-be12-4ed13a104c8a;REPLAY REPRODUCED; LIVE NO_VALID_ANCHOR(expected).
- CLI evidence:docs/cli_validation.json; human-readable demo:docs/demo_report.md;15-category acceptance:docs/test_results.md.
- Final synthetic backtest:2 tasks,12 records,0 failures; unavailable real dataset rejected.
- Secret scan found no supplied API keys in code/config/docs/tests/templates/dashboard/scripts/migrations.
- No unresolved automated test failures. Real-data/calibration limitations persist and are documented, not filled with fiction.

## Iteration 4 — Qwen switch requested by user
- User reports existing key is valid and upstream DeepSeek-V4-Pro is down; requests Qwen3.8-Max.
- Corrected earlier diagnosis: HTTP401 from api.deepseek.com does not prove platform credential invalid.
- Added shared JSON extractor/Qwen adapter, configurable regional endpoint, Qwen secret redaction; default pipeline and smoke now Qwen.
- Migrated local ignored .env to QWEN_* with existing platform key. No key emitted.
- Mock provider suite:9 passed. Real QwenCloud Singapore smoke:401; Tavily200. Asked for actual platform/Base URL; no further endpoints probed.
- Full regression/static checks pending result recording below.

- User supplied actual endpoint:https://maas.qianwenaiapi.com/compatible-mode/v1. Updated .env and checked-in defaults/example.
- Real smoke succeeded HTTP200; qwen3.8-max extracted1 synthetic claim; independent verifier accepted1;1324 total tokens. Existing key confirmed usable.
- Full regression:61 passed,0 failed; core coverage98.72%;mypy57 source files clean. No numerical forecasting changes.

## NPM availability recheck — 2026-11-07
- User asked whether missing verified NPM data means LLM cannot access target page.
- Database query confirmed observations=0. Provider is manual-import-only, not a live page-fetch implementation.
- Direct public GET returned200 (2095-byte JS app shell); browser rendered OpenAI Valuation $1.281T, As of Nov4,2026, with no login. Visual screenshot confirmed both fields.
- Corrected blanket inaccessible/403 interpretation. Access check saved in docs/npm_access_check.json. No observation imported in this diagnostic turn.

## 当前检查点：真实 NPM → LIVE → 重放（2026-11-07，替代此前缺口描述）
- 新增公开浏览器采集、可显式导入浏览器导出的原始证据；PNG/JPEG、HTML、文本及 SHA256 manifest 全部留存。
- Python Chromium 本机访问403；普通浏览器无需登录成功。实际视觉复核为 OpenAI NPM Valuation 1.281T，As of Nov 4, 2026。
- 实际采集 2026-11-06T21:39:31.414Z（新加坡11月7日05:39:31）；首次入库 2026-11-06T21:40:41.559932Z。有效日期2026-11-04独立记录，无精确原始发布时间；不可用于采集前的历史预测。
- observations 已有1条真实 VERIFIED 记录 d5d14081-4579-4295-8fa2-990a9acb433e。不是官方API认证；核验依据为DOM、截图视觉复核与归档哈希。
- LIVE a0a0a9bb-2445-45fc-ae8c-730e1c4423e8：COMPLETED，LIVE_PROSPECTIVE，synthetic=false，截止2026-11-07T02:17:38.390896Z。
- Tavily真实检索7次，16篇候选均因域名未在已审阅列表而只保存元数据；0次LLM调用、0新增有效主张。保留NPM_FETCH_BLOCKED和BASELINE_ONLY，不声称本次执行了真实新闻LLM抽取。
- 15个快照文件哈希及嵌套NPM证据哈希一致；概率和1；禁用HTTP和浏览器网络的REPLAY为REPRODUCED，完整结果哈希一致。
- 67项测试通过，ruff、mypy通过；新增测试覆盖日期与采集时间分离、历史不可见性、重复导入、篡改拒绝、吸收日期边界与脱离原始目录重放。
- 报告 docs/live_report.md；审计 docs/live_validation.json；原始证据和不可变快照在 data/snapshots/a0a0a9bb-2445-45fc-ae8c-730e1c4423e8。
- 当前指定链路已完成，但自动Python采集仍受403限制；真实新闻证据更新、长期历史样本和校准不是本次完成结果。下次先读本检查点，无需重复API凭据测试或导入同一报价。

## 迭代：按 V1 修正证据可信度评估（2026-11-07）
- 用户明确要求：再次按 Prompt_V1.md 的证据流程修改实现，不得在抓取正文前一律排除其他域名；本要求与结果纳入 Codex 开发记录。
- 已移除 `ALLOWED_DOMAINS` 的先验拒绝；官方/重点媒体优先抓取，并保留 `source_priority` 审阅标记。对其他公开域名同样检查 URL、robots、HTTP、HTML、正文和页面内发布时间；搜索摘要仍不作为正文。
- 非 OpenAI 官方文章记为 `unclassified_publication`，不直接宣称 `original_reporting`。主张照常走 Pydantic、引文、估值数值/口径、时间与来源核验；来源层级不是自动概率权重。
- 旧库中 `METADATA_ONLY` 的不可变来源记录无需改写；新增可访问正文版本在版本元数据中保留 `ACCESSIBLE`、来源类型和发布者，冻结输入按版本读取。旧预测快照保持原代码指纹；严格重放需恢复原代码版本。
- 增加非优先域名正文获取、摘要隔离、缺失时间、robots、跳转、本地地址拒绝，以及旧元数据版本升级为可核验正文版本的测试。69 项测试通过；ruff、mypy 通过。
- 尚未宣称其他域名报道的事实已被独立证实。真实性、共同匿名信源、转载与复杂口径仍按 V1 保守审阅；没有可核验正文和时间时不进入概率更新。

## 第二次真实 LIVE 核查（2026-11-07，证据准入修正后）
- run_id a811680a-d68e-457c-84f0-9a58fdc742aa，状态 COMPLETED；使用已核验的 NPM 1.281T（有效日2026-11-04）。
- Tavily 7次成功，14个不重复新闻候选；新逻辑未按非优先域名直接拒绝。网页采集结果：8个访问受限/跳转、2个robots不可核验、4个页面发布时间缺失；合格正文0，LLM调用0，入库主张0。
- 自动NPM刷新仍返回 NPM_FETCH_BLOCKED；本次结果 BASELINE_ONLY、UNCALIBRATED。不得称为新闻影响已经验证。
- 15个快照文件哈希校验通过，概率和1，禁用HTTP/浏览器访问的离线重放 REPRODUCED，结果哈希匹配。
- 详见 docs/live_validation_after_evidence_change.json 与 docs/live_report_after_evidence_change.md；快照在 data/snapshots/a811680a-d68e-457c-84f0-9a58fdc742aa。
- 当前明确剩余瓶颈：公开文章的访问限制和页面内可核验发布时间。不得用Tavily搜索日期或摘要冒充原文事实。
