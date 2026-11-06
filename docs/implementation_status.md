# Implementation status / 中断重连检查点

更新时间：2026-11-07（Asia/Singapore）。需求：Prompt_V1.md；含密钥，勿输出末尾API段。

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
无经用户核验的真实NPM观测/档案，提供空白导入模板。旧测试曾向DeepSeek官方域名发送平台密钥，401不能据此证明密钥失效。已用用户指定平台成功调用Qwen3.8-Max：HTTP200，1条合成主张抽取及独立核验通过。NPM页面403，无授权API。所有likelihood/alpha/jump未校准，因果效应未识别，M5校准NOT_FITTED。

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
- 本次代码交付已完成；后续接入真实数据/凭据后再验证实际LIVE与校准。

## 用户追加要求：切换Qwen3.8-Max（2026-11-07）
- 默认orchestrator和smoke脚本改用QwenExtractor，模型qwen3.8-max；保留schema、核验、预算和概率引擎。
- 新增QWEN_API_KEY/QWEN_MODEL/QWEN_BASE_URL，兼容DASHSCOPE_API_KEY；本地.env复用用户提供的平台密钥，不输出或提交。
- Qwen参数为enable_thinking=false、max_completion_tokens=2500、JSON object；不发送DeepSeek专用thinking参数。
- 用户明确Base URL为https://maas.qianwenaiapi.com/compatible-mode/v1，默认配置与.env已更新。真实smoke HTTP200，claim_count=1、verified_claim_count=1。
- 新代码指纹与旧版本不同，旧快照仍保留；严格重放旧运行需恢复原代码版本。

- Qwen切换验收：61项测试通过、ruff/mypy通过。现有密钥可用，无需更换；正式LIVE仍需真实NPM核验数据。
