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
- [x] 最新已完成56测试通过，核心覆盖率99.23%，ruff/mypy通过。
- [x] 真实API smoke：Tavily200；DeepSeek401，docs/api_smoke.json。
- [x] 合成回测2任务×6模型=12记录，0失败；真实档案缺失正确拒绝。
- [ ] 最后复查后的完整重跑、最终DEMO/REPLAY报告、交付记录（进行中）。

## 真实限制
无经用户核验的真实NPM观测/档案，提供空白导入模板。DeepSeek真实凭据认证失败。NPM页面403，无授权API。所有likelihood/alpha/jump未校准，因果效应未识别，M5校准NOT_FITTED。

## 重连继续
1. 读本文件、docs/work_log.md、docs/adr/0001-conservative-research-boundaries.md。
2. 使用.venv/Scripts/python；运行pytest、ruff、mypy。pytest临时目录在项目data/test-tmp。
3. 继续未勾选项，保存最终测试数和DEMO报告，不重做完成模块。
4. 不输出.env或prompt密钥，不用合成数据填LIVE缺口。
5. replay要求相同代码内容和依赖；早期开发快照可能因代码演进不能重放，属预期检查。
