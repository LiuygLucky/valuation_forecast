# ADR 0002 — 用户指定切换 Qwen3.8-Max

2026-11-07：用户要求改用Qwen3.8-Max，并提供实际Base URL：`https://maas.qianwenaiapi.com/compatible-mode/v1`。

默认QwenExtractor / qwen3.8-max；QWEN_BASE_URL可覆盖接口，QWEN_API_KEY或DASHSCOPE_API_KEY从环境读取。本地.env继续使用用户原平台密钥。保留DeepSeekExtractor仅供显式注入，不自动回退。

请求JSON object、temperature=0、enable_thinking=false、max_completion_tokens=2500；继续Pydantic及独立来源/引文/数值/时间核验，最多两次schema重试。不改变预测目标或概率模型。

真实用户接口HTTP200；抽取1条合成测试主张并通过独立核验，见api_smoke_qwen.json。此前DeepSeek官方域名和QwenCloud新加坡域名401不能证明平台密钥失效，也不能诊断模型服务故障。

参数参考：https://docs.qwencloud.com/developer-guides/text-generation/structured-output 与 https://docs.qwencloud.com/developer-guides/text-generation/thinking；实际endpoint由用户提供并已验证。
