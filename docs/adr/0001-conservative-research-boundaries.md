# ADR 0001 — V1 实施边界（2026-11-07）

记录必要工程取舍，不改变 Prompt_V1.md 的目标、金融口径、情景分解或技术栈。

- DeepSeek 使用 HTTPX 调用 OpenAI 兼容 REST；Tavily 使用官方 REST。便于完整 mock 请求和失败，不强制引入 SDK。默认 deepseek-v4-pro，JSON object、temperature=0、关闭 thinking；真实可用性由 smoke test 决定。
- 显式 as_of 只读取当时已经入库/可见的版本，不搜索今天的网页。省略 as_of 的 LIVE 在采集后冻结 cutoff；回溯调用不能作为事前提交评分。
- 今天导入历史截图，first_seen_at/retrieved_at 是今天；原采集时间保留在元数据。历史档案另有 archive_capture_at/archive_verified，不以回填系统首次可见时间代替认证。
- 无历史拟合数据，beta=0；情景权重、宽 mu/sigma/jump/pass-through/lag、似然和 alpha 均为 heuristic。敏感性不是参数后验。M5 不冒称经验校准，标记 NOT_FITTED。
- 默认仅启用 scenario_weight 通道；conditional_value 映射表为空。缺少独立成交事实和联合模型时，不因同一新闻同时改权重和跳跃中心。
- 实时 Agent 按 OpenAI/指标族/2026 保守合并经济事件，防止 LLM 编造事件 ID 获得多次更新。可能过度合并不同交易；未来需人工审核独立交易身份后放开。
- 自动正文只获取预先批准的官方和高优先级域名，尊重 robots，不追随未经审查的重定向，不越过付费墙。不明时间或无正文只存元数据。
- 初始迁移使用冻结 SQL；后续变更增加新迁移，不让旧迁移随 ORM 改变。SQLite 防误操作，不保证抵抗磁盘管理员篡改。
- 辅助回测可多公司/日期，正式 Dashboard 仍只有原固定问题。SYNTHETIC、RETROSPECTIVE_WEAK、HISTORICAL_ARCHIVED 和不同指标来源分组评分。

未采用的替代方案：自由 Agent 概率、未授权 NPM 接口、融资报道替代 NPM、无数据的因果效应估计、强行训练时序大模型。
