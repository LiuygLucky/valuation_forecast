# 来源注册（2026-11-07）

|来源|用途|状态与限制|
|---|---|---|
|NPM 指定页面|唯一目标和结算指标|开发访问403；未发现已获授权稳定官方API，提供人工核验导入|
|OpenAI 官方新闻|优先一手证据|仅合法正文和元数据；不是NPM结算值|
|Reuters/Bloomberg/FT|原始报道|付费墙/robots/受限重定向只记录元数据|
|Nasdaq 官方|平台方法|公开股市日历不能证明NPM更新时间|
|Tavily|搜索发现|摘要不是正文；真实smoke HTTP200|
|DeepSeek|结构化抽取|schema和规则验证；真实smoke HTTP401|

官方文档查阅：

- [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) 列出 deepseek-v4-pro、base URL及JSON能力；不证明当前密钥有权限。
- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search) 定义endpoint、Bearer认证和参数。
- [NPM目标页](https://fe.secondmarket.com/companies/company-30839e0b-2730-4495-839f-1bf638fa9cca/data) 未取得合格估值，不推断价格。

真实验证保存在api_smoke.json，不含密钥、认证头或原始错误响应。服务可访问性不等于预测准确性。
