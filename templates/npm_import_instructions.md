# 真实 NPM 人工导入

模板只有表头。每行必须来自你有权访问的 NPM 页面或导出，不要填写演示价格。

|字段|要求|
|---|---|
|observed_on|纽约 YYYY-MM-DD，与 observed_at 对应|
|valuation_trillion|正数，万亿美元，保留原始精度|
|observed_at|指标观测时间，带 Z 或明确 UTC offset|
|captured_at|实际采集时间，带时区；不得早于观测或晚于导入时点|
|url|task_config.yaml 中固定 NPM URL|
|artifact_path|存在且非空的截图/导出文件，相对路径相对于 CSV|
|operator|实际操作人|
|methodology|页面 Valuation 方法、指示性/估算说明，或明确尚未确认|
|review_status|VERIFIED / UNVERIFIED|
|reviewer|VERIFIED 必填实际复核人|
|ingestion_method|manual_csv / manual_entry / authorized_export|
|metric_type|npm_valuation|
|indicative|按已核验方法填写，通常 true|
|synthetic|真实导入必须 false，合成 fixture 不经过此入口|
|archive_capture_at|可选，已认证历史档案捕获时间，不是新闻发布时间|
|archive_verified|仅有档案时间证明且实际复核时 true|

导入复制原始证据并计算 SHA256，Decimal 金额以文本保存。今天导入旧截图，first_seen_at 仍是今天；另有认证档案才能支持严格历史回测。缺资料保持缺失。
