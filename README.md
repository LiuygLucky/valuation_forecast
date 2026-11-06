# OpenAI NPM Valuation Forecast · V1

固定问题：**OpenAI 在 2026-12-31 的 Nasdaq Private Market Valuation 属于哪个区间？**

这是可审计、可重放的本地研究原型。DEMO 全为合成数据；参数未经过历史拟合或概率校准。融资估值、企业价值、股价不能替代 NPM Valuation。流程：结构化数据 → Student-t 锚定跳跃混合 → 证据抽取核验 → 来源/事件去重 → 因果机制映射 → 一次性情景似然更新 → 报告。

## 当前状态

- Python 包、SQLite/Alembic、NPM 人工导入、金融基线、Evidence Agent、DAG、审计快照、CLI、Streamlit、结算评分、回测和消融接口已实现。
- 真实接口记录见 [docs/api_smoke.json](docs/api_smoke.json)：Tavily 成功；提供的 DeepSeek 凭据返回 HTTP 401，需要有效的 DeepSeek 官方 API 凭据。
- 未提供经核验真实 NPM 观测/历史档案，LIVE 报告 NO_VALID_ANCHOR；禁止样例价格填缺口。
- 重连入口：[实施清单](docs/implementation_status.md)、[工作记录](docs/work_log.md)。验收结果见 [docs/test_results.md](docs/test_results.md)。

## 安装（Windows PowerShell，Python 3.12）

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

已有 `.env` 时保留它。只在 `.env` 或环境变量中设置 TAVILY_API_KEY、DEEPSEEK_API_KEY。原 prompt 含凭据，`.gitignore` 同时排除 `.env` 和 `Prompt_V1.md`；代码、日志和 manifest 不复制凭据。

严格锁定依赖：

```powershell
python -m pip install uv
uv sync --locked --extra dev
```

可选研究依赖不参与核心安装，无需 GPU。命令在项目根目录执行；开发安装从根目录读取 configs/ 和 alembic/。

## 演示、重放与界面

```powershell
.venv\Scripts\python -m forecast.cli init-db
.venv\Scripts\python -m forecast.cli forecast --mode demo --as-of 2026-11-07T12:00:00-05:00
.venv\Scripts\python -m forecast.cli list-runs
.venv\Scripts\python -m forecast.cli replay --run-id <运行UUID>
.venv\Scripts\python -m streamlit run dashboard/app.py --server.address 127.0.0.1
```

也可双击 `start_dashboard.bat`。固定题面，选择 LIVE/DEMO 后一键运行；展示六区间图表、概率总和、情景、接纳/重复/超时/吸收证据、来源、敏感性、覆盖矩阵、报告下载和结算状态。

DEMO 锚点 1.20T 和新闻都是**虚构示例**，样例见 `tests/fixtures/synthetic_demo.json`，不写入真实市场观测表。每次预测有不同 UUID，快照位于 `data/snapshots/<uuid>/`。重放离线验证文件/manifest 哈希、代码指纹、依赖版本和数值结果；代码/依赖改变会明确拒绝，需要恢复记录版本后重放。

## 真实 NPM 导入与 LIVE

`templates/npm_import_template.csv` 只有表头，不含伪装真实的价格；字段见 `templates/npm_import_instructions.md`。

1. 在有权访问的 NPM 页面手工采集/导出，保留截图或导出文件。
2. 按真实日期填写估值、观测/截图时间、指标方法、操作人和复核人。
3. VERIFIED 必须复核；UNVERIFIED 仅用于 PROVISIONAL。程序校验格式/哈希，不能代替人的真实性复核。

```powershell
.venv\Scripts\python -m forecast.cli import-npm --csv data/imports/npm.csv
.venv\Scripts\python -m forecast.cli forecast --mode live
.venv\Scripts\python -m forecast.cli forecast --mode provisional
```

显式 `--as-of` 只读已封存知识，不抓当前网页冒充过去；实时采集省略此参数。NPM 默认返回 NPM_FETCH_BLOCKED，不探测私有 API。外部服务失败有类型健康记录；已有核验锚点仍可运行 baseline-only，不宣称搜索成功。

预算：7 个固定主题，每主题3条，总文档21，最多10文档送 LLM。搜索每请求最多3次尝试、总21基础 credits；LLM 每文档最多3次结构化尝试、每次输出上限2500 tokens。相同来源版本不重复抽取。

## 时间与结算

- 内部 UTC，业务使用 America/New_York 自动 DST。13:00 ET 是任务提供的待确认更新时间。
- 0.85→B2，1→B3，1.15→B4，1.30→B5，**1.45→B5**，严格大于1.45→B6；不先四舍五入。
- 首次合格 LIVE 冻结任务配置到 `data/frozen_task_config.json`。
- 冻结：2026-12-31 12:59:59 ET；13:00 ET 后方可结算。只用目标日或之前最后合格 NPM 观测，可晚采集档案，但有效日期不能越过目标日。

```powershell
.venv\Scripts\python -m forecast.cli settle --target-date 2026-12-31
# 没有可确认值则记录 UNRESOLVED，不评分。
.venv\Scripts\python -m forecast.cli settle --valuation <真实值> --source-id <导入ID> --confirm-final-observation --method-note "复核过程及最后合格观测依据"
```

仅冻结前实际封存的实时 LIVE 进入主任务正式评分，DEMO/暂定/回溯调用不混入。Brier 不除类别数，Log Loss epsilon=1e-12，RPS 不归一化。

## 测试与研究

```powershell
.venv\Scripts\python -m pytest -q --cov=forecast.domain --cov=forecast.model --cov=forecast.audit --cov-report=term-missing
.venv\Scripts\python -m ruff check src tests dashboard scripts
.venv\Scripts\python -m mypy src/forecast
.venv\Scripts\python -m forecast.cli backtest --dataset tests/fixtures/synthetic_backtest.json
.venv\Scripts\python -m forecast.cli ablation --dataset tests/fixtures/synthetic_backtest.json
.venv\Scripts\python scripts/smoke_providers.py
```

只有最后一个命令调用真实 API（可能产生少量费用）；测试离线、外部调用 mock。回测演示为 SYNTHETIC，不代表预测能力。真实 dataset 契约见 `docs/api_contracts.md`；缺数据返回 DATA_UNAVAILABLE。M0–M5 同切点/同测试集；M5 校准标记 NOT_FITTED。单一 OpenAI 目标不能证明校准。

## 中断恢复

重连先读 `docs/implementation_status.md` 和 `docs/work_log.md`，再运行测试，继续未完成项。

运行时先落盘来源版本，冻结后计算不读实时数据；输出先临时目录，再原子重命名和数据库事务索引。异常记录 FAILED；强杀进程可能遗留 RUNNING，确认无运行中作业后执行 `python -m forecast.cli recover`，将超过2小时的 RUNNING 标记 INTERRUPTED_PROCESS。已完成快照不覆盖；有目录但无成功数据库索引的是孤立计算结果，不是正式预测。

防误写不等于防磁盘管理员恶意篡改；重要正式预测需外部只读存储或独立提交哈希证明时间。
