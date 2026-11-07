## 最新增量验收：Qwen3.8-Max切换

2026-11-07：**61 passed，0 failed；核心覆盖率98.72%（391 statements，5 uncovered）**。ruff/mypy通过。新增Qwen路由/请求参数/schema重试/错误处理/环境读取/脱敏测试。真实用户接口HTTP200，抽取1条合成主张且独立核验通过；见api_smoke_qwen.json。原DeepSeek401不证明密钥无效，现有密钥已在正确平台验证成功。

以下保留原V1验收记录：

# V1 验收记录 — 2026-11-07

**结果：58 passed，0 failed；核心 domain/model/audit 覆盖率 99.23%（391 statements，3 uncovered）。**

运行环境：Windows、Python3.12.7、本地.venv；依赖见uv.lock。mypy检查57个源码文件无错误，ruff全部通过，uv pip check确认67个已安装包兼容。Streamlit AppTest已实际加载页面并点击DEMO预测按钮，无异常。

## 真实执行的命令

```powershell
.venv\Scripts\python -m pytest -q --cov=forecast.domain --cov=forecast.model --cov=forecast.audit --cov-report=term-missing --cov-report=json:docs/coverage.json --junitxml=docs/test_results.xml
.venv\Scripts\python -m ruff check src tests dashboard scripts alembic
.venv\Scripts\python -m mypy src/forecast
.venv\Scripts\uv pip check
.venv\Scripts\python -m forecast.cli init-db
.venv\Scripts\python -m forecast.cli forecast --mode demo --as-of 2026-11-07T12:00:00-05:00
.venv\Scripts\python -m forecast.cli replay --run-id ff3de36d-8e8d-4a4b-be12-4ed13a104c8a
.venv\Scripts\python -m forecast.cli forecast --mode live --as-of 2026-11-06T20:00:00Z
.venv\Scripts\python -m forecast.cli backtest --dataset tests/fixtures/synthetic_backtest.json
.venv\Scripts\python -m forecast.cli backtest --dataset archived_v1
.venv\Scripts\python scripts/smoke_providers.py
```

## 原任务15类验收映射

|#|要求|测试/证据|结果|
|---|---|---|---|
|1|精确边界，1.45归B5|test_domain / test_probabilities|通过|
|2|六类概率有限非负和为1|test_model_evidence、各模式集成|通过|
|3|发布/首次可见/修订时间泄漏|test_domain、test_import_time、test_database_pipeline|通过|
|4|纽约夏令时|test_timezone_dst_and_naive|通过|
|5|Reuters+三转载只更新一次|test_reuters_plus_three_syndications_one_update|通过|
|6|投前/投后等口径不同不直接冲突|test_scope_conflicts_and_invalid_verification|通过|
|7|proposed→closed只使用当时状态|test_state_as_of_and_corrections|通过|
|8|结构化重合/可能吸收alpha=0|test_overlap_guard_and_channels、延迟转载回归|通过|
|9|离线冻结重放一致|test_demo_replay_offline_and_no_overwrite、CLI REPRODUCED|通过|
|10|相同日期新UUID、原哈希不改|不可变快照/数据库触发器测试|通过|
|11|外部失败类型明确、合格锚点baseline-only|test_disconnect_degrades_to_verified_baseline、provider mocks|通过|
|12|DEMO不混入LIVE|test_live_no_synthetic_and_provisional、真实空数据CLI|通过|
|13|LLM source/数值幻觉拒绝|test_providers、融资额不能充估值回归|通过|
|14|Brier/Log loss/RPS与1.45结算|test_evaluation、settlement集成|通过|
|15|先验/证据敏感性、固定seed|test_deterministic_valid_mixture_and_sensitivity|通过|

另外验证：重复迁移、SQLite WAL/外键、旧截图今天导入不回填first_seen、认证历史档案模式、主任务配置冻结、完整mock采集入库与LLM缓存、API密钥不进入交付文件。

## CLI、API和数据真实性

- DEMO运行：ff3de36d-8e8d-4a4b-be12-4ed13a104c8a，COMPLETED。
- REPLAY：REPRODUCED，完整结果哈希相同且不联网。
- LIVE显式历史切点：NO_VALID_ANCHOR，退出码2，符合无真实数据要求。
- 合成回测：2任务×6模型=12评分记录，0失败；SYNTHETIC不代表真实预测能力。
- 未提供archived_v1：DATA_UNAVAILABLE，预期失败；无伪造历史结果。
- 真实Tavily HTTP200；真实DeepSeek HTTP401。服务端认证未通过，不声称真实LLM抽取链已验证。
- 没有真实NPM观测；人工导入模板为空白。所有演示新闻、锚点和回测结果均为合成数据。
- 所有模型参数heuristic/UNCALIBRATED；causal_effect_not_identified；M5校准NOT_FITTED。

详见coverage.json、test_results.xml、cli_validation.json、api_smoke.json和demo_report.md。

## 遗留限制

真实端到端LIVE验收仍依赖合法可访问原文及至少一条经实际复核的NPM观测。LLM现已切换Qwen并验证成功。真实档案回测和参数拟合依赖用户持有的同口径历史数据。自动核验采取保守英文规则和事件族合并，复杂口径/信源关系需人工复核；不宣称生产级金融系统或已证明预测精度。上述限制已在运行报告和UI中标明。

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
