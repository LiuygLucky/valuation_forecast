from forecast.domain.bins import BIN_IDS


def render_report(
    run_id, mode, as_of, inputs, baseline, posterior, evidence, sensitivity, warnings
):
    label = "DEMO / SYNTHETIC — 纯合成演示，不是正式预测" if mode == "DEMO" else mode
    anchor = inputs["anchor"]
    lines = [
        f"# OpenAI NPM Valuation 预测报告 — {label}",
        "",
        "**UNCALIBRATED / heuristic / causal_effect_not_identified**",
        "",
        "固定目标：2026-12-31 NPM Valuation（USD trillion）。研究原型，不用于真实投资决策。",
        f"运行 ID：`{run_id}`；知识截止：`{as_of}`；数据质量：`{baseline['data_quality']}`。",
        "",
        f"锚点：{anchor['value']}T；来源 `{anchor['source_id']}`；日期 `{anchor['observed_at']}`；"
        f"年龄 {baseline['anchor_age_days']:.2f} 天。NPM 指示值不等于已成交或已完成融资。",
        "",
        "## 数据状态",
        "",
    ]
    lines.extend(f"- {w}" for w in warnings or ["无新增采集错误；不代表数据完整。"])
    lines.extend(["", "## 六区间概率", "", "|区间|先验|后验|MC SE|", "|---|---:|---:|---:|"])
    for k in BIN_IDS:
        lines.append(
            f"|{k}|{baseline['prior_bin_probs'][k]:.6%}|"
            f"{posterior['bin_probabilities'][k]:.6%}|{posterior['mc_se'][k]:.6f}|"
        )
    lines.extend(
        [
            "",
            f"概率总和：{sum(posterior['bin_probabilities'].values()):.12f}。",
            "区间：(0,.85)、[.85,1)、[1,1.15)、[1.15,1.30)、[1.30,1.45]、(1.45,+∞)。",
            "MC SE 是模拟误差，不是预测准确率置信区间。参数未拟合，未给出参数后验区间。",
            "",
            "## 情景混合",
            "",
            "|情景|先验权重|后验权重|条件估值 5% / 50% / 95%|",
            "|---|---:|---:|---|",
        ]
    )
    for s, prior in baseline["scenario_prior"].items():
        q = baseline["conditional_summaries"][s]
        lines.append(
            f"|{s}|{prior:.5f}|{posterior['scenario_posterior'][s]:.5f}|"
            f"{q['q05']:.4f} / {q['median']:.4f} / {q['q95']:.4f} T|"
        )
    q = posterior["predictive_quantiles"]
    lines.extend(
        [
            "",
            f"混合估值预测分位数：5%={q['q05']:.4f}T，50%={q['median']:.4f}T，95%={q['q95']:.4f}T。",
            "",
            "## 证据与排除原因",
            "",
        ]
    )
    for row in evidence:
        lines.append(
            f"- `{row['cluster_id']}`：{'接纳' if row['included'] else '排除/仅解释'}；"
            f"{row.get('exclusion_reason') or row['overlap_status']}；alpha={row['alpha']}；"
            f"channel={row['effect_channel']}；重复数={row.get('duplicate_count', 0)}；"
            f"机制={','.join(row.get('mechanism_path_ids', []))}。"
        )
        lines.append(f"  去重：{row['dedup_reason']}；假设：{row['claim']['hypothesis']}")
        for source in row["sources"]:
            lines.append(
                f"  来源：[{source['source_id']}]({source['canonical_url']})；"
                f"公开={source.get('published_at')}；首次可见={source.get('first_seen_at')}；"
                f"版本={source['version_id']}。"
            )
    if not evidence:
        lines.append("没有合法证据更新；posterior=prior。无新闻不能解释为无风险。")
    lines.extend(
        [
            "",
            "## 参数来源与敏感性",
            "",
            str(baseline["parameter_provenance"]),
            "",
            "所有 likelihood、alpha、jump、pass-through、lag 都是未校准 heuristic。beta=0，未识别。",
            "消息早于锚点并不证明已完全吸收；保守 alpha=0 可能低估信息作用。",
            "情景按 S1（已完成重大融资且重估）→S2（其他重估）→S3（其余）优先级互斥归类。",
            "同一事实仅进入一个效应通道；默认不同时调整跳跃中心。",
            "",
            "敏感性是不同假设的结果，不是统计置信区间：",
            "",
            "|设定|B1|B2|B3|B4|B5|B6|",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, probs in sensitivity.items():
        lines.append("|" + name + "|" + "|".join(f"{probs[k]:.4f}" for k in BIN_IDS) + "|")
    lines.extend(
        [
            "",
            "## 变化触发器与结算",
            "",
            "取得新核验 NPM 观测、融资状态变更、独立且有正文支持的新事实，或已审阅参数版本变化时重算。",
            "每次从 Financial Baseline 和有效 cluster 完整重算，不重复叠加昨天后验。",
            "冻结：2026-12-31 12:59:59 America/New_York。结算只接受截至目标日的合格 NPM 指标；",
            "结算采集时间可以晚于目标日，但必须有可复核档案和 effective_date。未核验则 UNRESOLVED，不评分。",
            "单个目标不能证明校准。数据、代码哈希、依赖、参数、seed 和排除清单见 manifest.json。",
            "",
        ]
    )
    return "\n".join(lines)
