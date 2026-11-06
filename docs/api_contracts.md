# 服务契约

`forecast.application.pipeline.forecast_once(as_of=None, mode="LIVE", *, engine=None, output_dir=None, providers=None, archived_inputs=None) -> PredictionRun`

- LIVE默认采集后冻结当前UTC；显式as_of只用已入库知识，标记STORED_AS_OF_ONLY，不是新事前预测。
- providers注入search/extractor/retriever/npm，均可mock；返回DataFetchResult(provider,status,data,http_status,reason)。
- DEMO不写入真实observations/claims；REPLAY用replay_run(run_id)，离线验证代码、依赖及哈希。
- HISTORICAL_ARCHIVED需要冻结输入、认证档案文件/哈希/捕获时间。没有证明拒绝。
- 错误包括SEARCH_FAILURE、LLM_FAILURE、REVIEW_REQUIRED、NPM_FETCH_BLOCKED、METADATA_ONLY、TIME_NOT_VERIFIED，不等于无新闻。

Claim的Pydantic schema禁止额外字段与概率。引文必须在正文；source_id必须存在；公开时间与source一致；金额与估值语境/币种/量纲绑定；closed有正文支持。数据库UTC ISO时间，Decimal金额文本，另存asof_et。17张需求表外还有健康/搜索/抽取审计表。

## 回测数据

JSON为 `{"tasks": [AuxiliaryTask, ...]}`；完整合成例见tests/fixtures/synthetic_backtest.json。

- task_id/company/metric/source_family/experiment；实验等级HISTORICAL_ARCHIVED、RETROSPECTIVE_WEAK、SYNTHETIC。
- 带时区as_of、target_date、settlement_value、settlement_effective_date、真实settlement_archive_uri/settlement_sha256。
- event_families用于purge；parameter_fitted_until如有须早于切点。
- inputs与快照一致：anchor/observations/features/claims/sources。所有引用匹配source版本；知识和观测时间不能越过切点。
- 严格档案需archive_capture_at/archive_verified/archive_uri/metadata_json.artifact_sha256；不能回填first_seen_at伪装过去。

M0–M5同任务/seed/截止，记录证据数、耗时、失败、离线API成本0和样本量。不同指标、来源和实验等级分组。少于默认100个辅助样本不提供ECE；足量后才提供有桶样本量的描述性top-label ECE。本版本校准NOT_FITTED。

## Qwen3.8-Max override (2026-11-07)
Default extraction provider is QwenCloud/QwenExtractor; model defaults to qwen3.8-max. Read QWEN_API_KEY or DASHSCOPE_API_KEY; QWEN_MODEL and QWEN_BASE_URL override model/regional compatibility root. Never reuse a legacy credential implicitly in provider code. The local .env migration explicitly reused the key under the user instruction. Requests use enable_thinking=false, max_completion_tokens=2500 and JSON object; initial attempt plus two schema retries. DeepSeekExtractor remains an explicit legacy adapter only.
