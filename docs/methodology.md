# 方法

1. 来源保留 UTC 知识时间、经济时间、不可覆盖版本和SHA256；选择截止时点最新核验 NPM 锚点。
2. SQLite 显式BEGIN建立一致性视图，冻结后不读实时数据。
3. `log(V)=log(anchor)+mu*h+sigma*sqrt(h_eff)*Z+jump*pass_through`，Student-t(df>2)标准化方差1，lag超过目标不传导；无已核验报价误差不用h_floor。
4. 互斥S1/S2/S3各生成20,000条件样本，beta=0未识别。D稀疏时使用未校准先验。
5. Tavily只发现来源。正文引文、时间、量纲、估值口径、状态、source_id独立验证后才形成claim；LLM supported不是likelihood。
6. 来源依赖/引用/经济事件连通分量保守去重；用最新可用状态，重复报道保留最早同事实时间。矛盾和corrected待复核。
7. 结构化重合、可能吸收、未来、时间不明、未注册机制等不更新概率。
8. 一次性计算 `log_w(s)=log P(S|D)+sum alpha_c*log L_c(s)`，logsumexp归一化；不叠加昨日后验。
9. `P(Bk|D,E)=sum P(Bk|S,D,E)*P(S|D,E)`。六区间非负有限，和误差<1e-10；1.45属于B5。
10. 保存样本、参数、知识时间、排除原因、来源/模型/依赖哈希、seed和报告。
11. 仅预注册NPM规则结算；UNRESOLVED不评分。Brier/Log loss/RPS不除类别数。辅助任务按时间purge并隔离共享事件族；档案、弱回溯、合成数据分组。
