# Implementation status / 中断重连检查点

更新时间：2026-11-07（Asia/Singapore）。需求：Prompt_V1.md；含密钥，勿输出末尾API段。

**最新状态：真实NPM已入库，LIVE完成且离线重放一致；详见文末“当前检查点”。此前“0观测/未验收”等为历史记录，已被该检查点替代。代码提交478b984。**

## 按需求顺序实施
- [x] 初始盘点只有Prompt_V1.md；Python3.12.7；已创建.venv和uv.lock。
- [x] task_config、六区间、UTC/DST、单位、严格schema及测试。
- [x] SQLAlchemy/SQLite WAL/外键、冻结Alembic迁移、源版本、NPM导入、不可覆盖审计。
- [x] 固定seed Student-t锚定跳跃混合、S1/S2/S3、样本和模拟误差。
- [x] 来源/事件聚类、一次性likelihood、重合/吸收、转载不增加概率。
- [x] 可mock Tavily/DeepSeek、固定预算、增量/覆盖回看、正文核验、来源图、状态链。
- [x] 预注册DAG、机制白名单、单效应通道、敏感性。
- [x] 原子快照/manifest、报告、CLI、Streamlit固定题面一键运行。
- [x] 五种运行模式、结算评分、辅助回测/消融接口。
- [x] 当前61测试通过，核心覆盖率98.72%，ruff/mypy通过。
- [x] 真实API smoke：Tavily200；DeepSeek401，docs/api_smoke.json。
- [x] 合成回测2任务×6模型=12记录，0失败；真实档案缺失正确拒绝。
- [x] 最终58测试通过；DEMO/REPLAY一致；验收报告、代码版本与交付记录已保存。

## 真实限制
无经用户核验的真实NPM观测/档案，提供空白导入模板。旧测试曾向DeepSeek官方域名发送平台密钥，401不能据此证明密钥失效。已用用户指定平台成功调用Qwen3.8-Max：HTTP200，1条合成主张抽取及独立核验通过。NPM重新检查：普通HTTP200，浏览器无需登录可见Valuation1.281T、有效日2026-11-04；数据库仍0条观测，尚未接入动态页面采集。所有likelihood/alpha/jump未校准，因果效应未识别，M5校准NOT_FITTED。

## 重连继续
1. 读本文件、docs/work_log.md、docs/adr/0001-conservative-research-boundaries.md。
2. 使用.venv/Scripts/python；运行pytest、ruff、mypy。pytest临时目录在项目data/test-tmp。
3. 继续未勾选项，保存最终测试数和DEMO报告，不重做完成模块。
4. 不输出.env或prompt密钥，不用合成数据填LIVE缺口。
5. replay要求相同代码内容和依赖；早期开发快照可能因代码演进不能重放，属预期检查。

## 最终交付
- 代码版本：af956d1（实现提交2c20111）；后续文档封存不改变模型代码。
- DEMO run_id：ff3de36d-8e8d-4a4b-be12-4ed13a104c8a。
- 报告：docs/demo_report.md；CLI验收：docs/cli_validation.json；测试映射：docs/test_results.md。
- 启动：双击start_dashboard.bat，或按README命令。
- 核心研究原型代码已交付，但不能认定V1全部要求已完成：真实NPM采集/入库、真实LIVE端到端验收及研究增强仍有缺口。

## 用户追加要求：切换Qwen3.8-Max（2026-11-07）
- 默认orchestrator和smoke脚本改用QwenExtractor，模型qwen3.8-max；保留schema、核验、预算和概率引擎。
- 新增QWEN_API_KEY/QWEN_MODEL/QWEN_BASE_URL，兼容DASHSCOPE_API_KEY；本地.env复用用户提供的平台密钥，不输出或提交。
- Qwen参数为enable_thinking=false、max_completion_tokens=2500、JSON object；不发送DeepSeek专用thinking参数。
- 用户明确Base URL为https://maas.qianwenaiapi.com/compatible-mode/v1，默认配置与.env已更新。真实smoke HTTP200，claim_count=1、verified_claim_count=1。
- 新代码指纹与旧版本不同，旧快照仍保留；严格重放旧运行需恢复原代码版本。

- Qwen切换验收：61项测试通过、ruff/mypy通过。现有密钥可用，无需更换；正式LIVE仍需真实NPM核验数据。

## NPM访问复核（2026-11-07）
已从用户指定页面直接看到OpenAI Valuation $1.281T，As of Nov4,2026；不是新闻替代值。纯HTTP只有JS页面框架，浏览器渲染可读，无需登录。当前NPM provider只提供人工导入路径，Qwen仅处理程序传入的摘录。该次核验记录在docs/npm_access_check.json，未将日期精度数据伪造为精确更新时间，也尚未写入observations。后续应接浏览器采集/证据留存并正确区分观测时间与指标有效日期。

## V1完成度复核
不能把61项自编测试通过或98.72%核心覆盖率等同于完整需求覆盖。NPM adapter当前仅人工导入，没有动态页面采集，已看到的真实值尚未入库；真实LIVE链路未完整验收。财务特征表/覆盖矩阵已有，经营与市场指标自动采集不足；事件依赖保守按指标族合并，复杂交易身份与冲突语义仍简化；回测/消融可运行但仅合成样本，M5没有拟合校准。beta=0、未识别因果效应及未启用PyMC/DoWhy/Darts本身是V1允许的低数据边界，不应误列为强制缺失。

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

## 最新开发检查点：新闻证据准入修正（2026-11-07）
用户要求依照 Prompt_V1.md 重做证据可信度实现，其他域名不得在正文抓取之前被一律拒绝。代码已将来源域名改为优先级标记；公开网页经 URL、robots、HTML、正文、发布时间检查后才进入 LLM 与独立规则核验。非官方来源不自动认定原创；旧元数据来源后来取得正文时用新不可变版本核验。69测试通过，ruff/mypy通过。历史 LIVE 报告描述的是当时的旧代码运行，不能据此推断本次新代码已完成真实新闻抓取；新代码需新的 LIVE 快照才能审计实际新闻结果。
