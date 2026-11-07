# OpenAI NPM Valuation 预测报告 — LIVE

**UNCALIBRATED / heuristic / causal_effect_not_identified**

固定目标：2026-12-31 NPM Valuation（USD trillion）。研究原型，不用于真实投资决策。
运行 ID：`d5e94b96-6a49-49ab-97cb-5df8890cb7f2`；知识截止：`2026-11-07T03:00:24.940607+00:00`；数据质量：`VERIFIED`。

锚点：1.281T；来源 `src_c4fe079327ff34c0bedc161c`；指标有效日期 `2026-11-04`；有效日期距知识截止 2 个纽约日历日。
实际观测时间 `2026-11-06T21:39:31.414000+00:00`；入库版本捕获时间 `2026-11-06T21:40:41.559932+00:00`。页面日期不等于精确更新时间；NPM 指示值不等于已成交或已完成融资。
公开浏览器采集的复核证据（如适用）：npm_page.png/jpg、npm_page.html、npm_page.txt、npm_capture.json；文件哈希见manifest。

## 数据状态

- NPM_FETCH_BLOCKED
- TIME_NOT_VERIFIED:PUBLICATION_TIME_MISSING
- BASELINE_ONLY: no eligible unabsorbed evidence likelihood
- UNCALIBRATED: expert_heuristic parameters
- NPM schedule is a page claim, not a guarantee; date-only quotes have no precise update timestamp

## 六区间概率

|区间|先验|后验|MC SE|
|---|---:|---:|---:|
|B1|0.396000%|0.396000%|0.000235|
|B2|1.860500%|1.860500%|0.000507|
|B3|9.460750%|9.460750%|0.001124|
|B4|44.631500%|44.631500%|0.002030|
|B5|30.971500%|30.971500%|0.001958|
|B6|12.679750%|12.679750%|0.001203|

概率总和：1.000000000000。
区间：(0,.85)、[.85,1)、[1,1.15)、[1.15,1.30)、[1.30,1.45]、(1.45,+∞)。
MC SE 是模拟误差，不是预测准确率置信区间。参数未拟合，未给出参数后验区间。

## 情景混合

|情景|先验权重|后验权重|条件估值 5% / 50% / 95%|
|---|---:|---:|---|
|S1|0.25000|0.25000|1.0143 / 1.3201 / 1.7493 T|
|S2|0.30000|0.30000|1.0323 / 1.2807 / 1.5908 T|
|S3|0.45000|0.45000|1.1657 / 1.2812 / 1.4080 T|

混合估值预测分位数：5%=1.0708T，50%=1.2856T，95%=1.5852T。

## 证据与排除原因

- `cluster_3f8aa655c408de38ddb36465`：排除/仅解释；REVIEW_REQUIRED；alpha=0.0；channel=explanation_only；重复数=1；机制=H10,H11,H12,H13。
  去重：same event/origin/citation; latest available state used once；假设：OpenAI is pursuing a $600 billion compute infrastructure goal, driving significant capital requirements and cash burn.
  来源：[src_cab529565fca2413538bf544](https://www.pymnts.com/news/artificial-intelligence/2026/openai-forms-jpmorgan-partnership-ahead-of-2027-ipo)；公开=2026-11-06T00:46:38+00:00；首次可见=2026-11-07T02:17:38.351499+00:00；版本=ver_549d69bf3d9bcd52f922de56。
  来源：[src_41ca9c9c0209da506091e866](https://techcrunch.com/2026/11/06/openai-reportedly-raises-an-additional-11-billion-at-a-1-25-trillion-valuation)；公开=2026-11-06T22:53:46+00:00；首次可见=2026-11-07T02:17:38.348502+00:00；版本=ver_ee9291e7b24ab7b01aed8cec。
  来源：[src_13f5c6ed7e5d3707ed56b755](https://tech-insider.org/openai-11-billion-funding-1-25-trillion-valuation-bloomberg-2026)；公开=2026-11-07T00:05:32+00:00；首次可见=2026-11-07T02:17:38.340309+00:00；版本=ver_786d1d515be650cbd866f81e。
- `cluster_dd577d06161e090235a7ffdd`：排除/仅解释；UNREGISTERED_MECHANISM；alpha=0.0；channel=explanation_only；重复数=1；机制=H05,H06,H07。
  去重：same event/origin/citation; latest available state used once；假设：OpenAI achieved $50B net annualized revenue last quarter, a 77% YoY increase driven by enterprise sales doubling
  来源：[src_711e9348b6b69b472c1ff55e](https://www.unite.ai/openais-enterprise-sales-take-majority-as-brockman-sees-ipo-readiness)；公开=2026-11-05T02:33:04+00:00；首次可见=2026-11-07T02:17:38.360516+00:00；版本=ver_e897b39485e3b44cab88ac42。
  来源：[src_18cc004b7309829c27d1c880](https://siliconangle.com/2026/11/06/openai-reportedly-raises-11b-in-new-funding-at-1-25t-valuation)；公开=2026-11-06T23:43:40+00:00；首次可见=2026-11-07T02:17:38.380891+00:00；版本=ver_d07973abf3a5bfcb8ee7194b。
- `excluded_claim_39e59638a75d5c666951412b`：排除/仅解释；REVIEW_REQUIRED；alpha=0.0；channel=explanation_only；重复数=0；机制=H03,H04。
  去重：REVIEW_REQUIRED；假设：OpenAI closed an initial $11 billion tranche of a planned up-to-$20 billion round at a $1.25 trillion post-money valuation.
  来源：[src_13f5c6ed7e5d3707ed56b755](https://tech-insider.org/openai-11-billion-funding-1-25-trillion-valuation-bloomberg-2026)；公开=2026-11-07T00:05:32+00:00；首次可见=2026-11-07T02:17:38.340309+00:00；版本=ver_786d1d515be650cbd866f81e。
- `excluded_claim_e132a6746d7f40d88747dace`：排除/仅解释；REVIEW_REQUIRED；alpha=0.0；channel=explanation_only；重复数=0；机制=H03,H04。
  去重：REVIEW_REQUIRED；假设：OpenAI committed $11B in new funding at an expected $1.25T valuation, with potential for up to $9B more
  来源：[src_18cc004b7309829c27d1c880](https://siliconangle.com/2026/11/06/openai-reportedly-raises-11b-in-new-funding-at-1-25t-valuation)；公开=2026-11-06T23:43:40+00:00；首次可见=2026-11-07T02:17:38.380891+00:00；版本=ver_d07973abf3a5bfcb8ee7194b。
- `excluded_claim_e39678b9791569748921ce28`：排除/仅解释；REVIEW_REQUIRED；alpha=0.0；channel=explanation_only；重复数=0；机制=H05,H06,H07。
  去重：REVIEW_REQUIRED；假设：OpenAI's enterprise sales have grown to constitute the majority of total company revenue as of November 2026.
  来源：[src_711e9348b6b69b472c1ff55e](https://www.unite.ai/openais-enterprise-sales-take-majority-as-brockman-sees-ipo-readiness)；公开=2026-11-05T02:33:04+00:00；首次可见=2026-11-07T02:17:38.360516+00:00；版本=ver_e897b39485e3b44cab88ac42。
- `excluded_claim_fe90603021db8df98cfef7c3`：排除/仅解释；REVIEW_REQUIRED；alpha=0.0；channel=explanation_only；重复数=0；机制=H03,H04。
  去重：REVIEW_REQUIRED；假设：OpenAI's ongoing funding round implies a valuation of $1.25 trillion based on $11 billion raised so far.
  来源：[src_41ca9c9c0209da506091e866](https://techcrunch.com/2026/11/06/openai-reportedly-raises-an-additional-11-billion-at-a-1-25-trillion-valuation)；公开=2026-11-06T22:53:46+00:00；首次可见=2026-11-07T02:17:38.348502+00:00；版本=ver_ee9291e7b24ab7b01aed8cec。

## 参数来源与敏感性

{'origin_type': 'elicited_prior', 'reviewer': 'UNREVIEWED_RESEARCH_ASSUMPTION', 'basis': 'No fitted NPM history; broad research assumptions only, not calibrated.'}

所有 likelihood、alpha、jump、pass-through、lag 都是未校准 heuristic。beta=0，未识别。
消息早于锚点并不证明已完全吸收；保守 alpha=0 可能低估信息作用。
情景按 S1（已完成重大融资且重估）→S2（其他重估）→S3（其余）优先级互斥归类。
同一事实仅进入一个效应通道；默认不同时调整跳跃中心。

敏感性是不同假设的结果，不是统计置信区间：

|设定|B1|B2|B3|B4|B5|B6|
|---|---:|---:|---:|---:|---:|---:|
|no_evidence|0.0040|0.0186|0.0946|0.4463|0.3097|0.1268|
|low|0.0040|0.0186|0.0946|0.4463|0.3097|0.1268|
|base|0.0040|0.0186|0.0946|0.4463|0.3097|0.1268|
|high|0.0040|0.0186|0.0946|0.4463|0.3097|0.1268|
|prior_sigma_low|0.0011|0.0095|0.0761|0.4964|0.3163|0.1005|
|prior_sigma_high|0.0082|0.0279|0.1125|0.4037|0.2946|0.1531|
|partial_absorption_alternative|0.0040|0.0186|0.0946|0.4463|0.3097|0.1268|

## 变化触发器与结算

取得新核验 NPM 观测、融资状态变更、独立且有正文支持的新事实，或已审阅参数版本变化时重算。
每次从 Financial Baseline 和有效 cluster 完整重算，不重复叠加昨天后验。
冻结：2026-12-31 12:59:59 America/New_York。结算只接受截至目标日的合格 NPM 指标；
结算采集时间可以晚于目标日，但必须有可复核档案和 effective_date。未核验则 UNRESOLVED，不评分。
单个目标不能证明校准。数据、代码哈希、依赖、参数、seed 和排除清单见 manifest.json。
