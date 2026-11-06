# 假设与局限

固定 OpenAI / NPM Valuation / 2026-12-31。指标不等于融资估值、企业价值或成交价。13:00 ET 更新说法来自任务，未独立核实；纽约冬季UTC-5、夏季UTC-4。

没有真实 NPM 数据集或独立历史训练/验证集。elicited_prior 是未审阅宽研究假设（reviewer=UNREVIEWED_RESEARCH_ASSUMPTION），不是专家共识或拟合结果。

log估值由锚点、漂移、单位方差 Student-t 噪声和有限跳跃构成。beta=0，未识别。mu/sigma/jump/pass-through/lag 在配置区间采样，滞后超过目标的冲击不生效。情景可上涨/下跌；S1/S2/S3 优先级及重大阈值预注册。proposed 不是 closed。

低样本的固定情景 prior 是 P(S|D) 的保守起点，不声称由 NPM 历史拟合。likelihood 和 alpha=0.35 都是 heuristic。早于锚点时 alpha=0 仅防重算，不证明充分吸收；报告比较证据强度、部分吸收和先验波动的替代设定。

MC SE 采用独立情景样本的分层方差：sqrt(sum_s w_s^2 p_sk(1-p_sk)/N_s)。展示概率是条件经验分布的加权混合；另保存抽取的先验/后验样本，其直方图可能存在额外模拟误差。估值分位数来自混合样本。没有参数后验，parameter_q05/q95 保持 null，不把敏感性当置信区间。

因果图是 SCM-lite 假设，含时序、滞后和混杂说明，causal_effect_not_identified。未执行 DoWhy 因果效应估计、PyMC 拟合、Darts 训练；extras 不影响核心安装。

机械引文/数值/日期核验不是完善语义理解。复杂金融条款、匿名信源独立性和矛盾仍需人工复核。保守事件族合并可能低估独立证据作用。
