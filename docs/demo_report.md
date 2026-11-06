# OpenAI NPM Valuation 预测报告 — DEMO / SYNTHETIC — 纯合成演示，不是正式预测

**UNCALIBRATED / heuristic / causal_effect_not_identified**

固定目标：2026-12-31 NPM Valuation（USD trillion）。研究原型，不用于真实投资决策。
运行 ID：`ff3de36d-8e8d-4a4b-be12-4ed13a104c8a`；知识截止：`2026-11-07T17:00:00+00:00`；数据质量：`DEMO`。

锚点：1.20T；来源 `synthetic_npm`；日期 `2026-11-04T17:00:00+00:00`；年龄 3.00 天。NPM 指示值不等于已成交或已完成融资。

## 数据状态

- DEMO/SYNTHETIC: all observations and news are fictional
- UNCALIBRATED
- UNCALIBRATED: expert_heuristic parameters
- NPM update schedule 13:00 ET is unconfirmed

## 六区间概率

|区间|先验|后验|MC SE|
|---|---:|---:|---:|
|B1|0.741250%|0.796655%|0.000342|
|B2|3.993250%|4.256784%|0.000777|
|B3|22.155500%|22.423677%|0.001699|
|B4|53.243750%|51.513079%|0.001891|
|B5|13.356500%|13.924781%|0.001359|
|B6|6.509750%|7.085025%|0.000953|

概率总和：1.000000000000。
区间：(0,.85)、[.85,1)、[1,1.15)、[1.15,1.30)、[1.30,1.45]、(1.45,+∞)。
MC SE 是模拟误差，不是预测准确率置信区间。参数未拟合，未给出参数后验区间。

## 情景混合

|情景|先验权重|后验权重|条件估值 5% / 50% / 95%|
|---|---:|---:|---|
|S1|0.25000|0.28216|0.9509 / 1.2364 / 1.6371 T|
|S2|0.30000|0.30889|0.9682 / 1.1997 / 1.4885 T|
|S3|0.45000|0.40895|1.0925 / 1.2002 / 1.3183 T|

混合估值预测分位数：5%=1.0012T，50%=1.2049T，95%=1.4930T。

## 证据与排除原因

- `cluster_73df46015e8858aceb2fab08`：排除/仅解释；PARTIALLY_OR_POSSIBLY_ABSORBED；alpha=0.0；channel=explanation_only；重复数=0；机制=H05,H06,H07。
  去重：same event/origin/citation; latest available state used once；假设：Illustrative uncalibrated mechanism
  来源：[synthetic_absorbed](https://example.invalid/synthetic/absorbed)；公开=2026-11-02T17:00:00+00:00；首次可见=2026-11-02T17:00:00+00:00；版本=synthetic_absorbed_v1。
- `cluster_87c5e2c5bf7ed0eb7f525712`：接纳；NEW_INFORMATION；alpha=0.35；channel=scenario_weight；重复数=1；机制=H03,H04。
  去重：same event/origin/citation; latest available state used once；假设：Illustrative uncalibrated mechanism
  来源：[synthetic_accepted](https://example.invalid/synthetic/accepted)；公开=2026-11-06T17:00:00+00:00；首次可见=2026-11-06T17:00:00+00:00；版本=synthetic_accepted_v1。
  来源：[synthetic_duplicate](https://example.invalid/synthetic/duplicate)；公开=2026-11-06T17:00:00+00:00；首次可见=2026-11-06T17:00:00+00:00；版本=synthetic_duplicate_v1。
- `excluded_synthetic_claim_future`：排除/仅解释；EXCLUDED_FUTURE；alpha=0.0；channel=explanation_only；重复数=0；机制=H03,H04。
  去重：EXCLUDED_FUTURE；假设：Illustrative uncalibrated mechanism
  来源：[synthetic_future](https://example.invalid/synthetic/future)；公开=2026-11-08T17:00:00+00:00；首次可见=2026-11-08T17:00:00+00:00；版本=synthetic_future_v1。

## 参数来源与敏感性

{'origin_type': 'elicited_prior', 'reviewer': 'UNREVIEWED_RESEARCH_ASSUMPTION', 'basis': 'No fitted NPM history; broad research assumptions only, not calibrated.'}

所有 likelihood、alpha、jump、pass-through、lag 都是未校准 heuristic。beta=0，未识别。
消息早于锚点并不证明已完全吸收；保守 alpha=0 可能低估信息作用。
情景按 S1（已完成重大融资且重估）→S2（其他重估）→S3（其余）优先级互斥归类。
同一事实仅进入一个效应通道；默认不同时调整跳跃中心。

敏感性是不同假设的结果，不是统计置信区间：

|设定|B1|B2|B3|B4|B5|B6|
|---|---:|---:|---:|---:|---:|---:|
|no_evidence|0.0074|0.0399|0.2216|0.5324|0.1336|0.0651|
|low|0.0077|0.0413|0.2229|0.5238|0.1364|0.0680|
|base|0.0080|0.0426|0.2242|0.5151|0.1392|0.0709|
|high|0.0085|0.0452|0.2268|0.4979|0.1449|0.0767|
|prior_sigma_low|0.0031|0.0282|0.2061|0.5834|0.1274|0.0518|
|prior_sigma_high|0.0157|0.0573|0.2329|0.4547|0.1478|0.0916|
|partial_absorption_alternative|0.0082|0.0435|0.2256|0.5094|0.1411|0.0723|

## 变化触发器与结算

取得新核验 NPM 观测、融资状态变更、独立且有正文支持的新事实，或已审阅参数版本变化时重算。
每次从 Financial Baseline 和有效 cluster 完整重算，不重复叠加昨天后验。
冻结：2026-12-31 12:59:59 America/New_York。结算只接受截至目标日的合格 NPM 指标；
结算采集时间可以晚于目标日，但必须有可复核档案和 effective_date。未核验则 UNRESOLVED，不评分。
单个目标不能证明校准。数据、代码哈希、依赖、参数、seed 和排除清单见 manifest.json。
