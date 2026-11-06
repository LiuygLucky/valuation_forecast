from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from forecast.application.pipeline import forecast_once
from forecast.audit.snapshot import read_snapshot
from forecast.config import ROOT, load_config
from forecast.db.models import EvaluationScore, PredictionRunRecord, ProviderHealth, Settlement
from forecast.db.queries import freeze_inputs
from forecast.db.session import init_db
from forecast.domain.time_policy import ET, utc

load_dotenv(ROOT / ".env", override=False)
st.set_page_config(page_title="OpenAI NPM 估值预测", layout="wide")
cfg = load_config()
engine = init_db()
now = datetime.now(UTC)
st.title("OpenAI · 2026-12-31 NPM Valuation")
st.caption("固定六区间 · 研究原型 · UNCALIBRATED · 非投资决策工具")
st.write(f"纽约时间：{now.astimezone(ET):%Y-%m-%d %H:%M:%S %Z} · 冻结：2026-12-31 12:59:59 ET")
st.link_button("NPM 目标指标页面", cfg.metric_url)
with Session(engine) as session:
    current = freeze_inputs(session, now)
anchor = current["anchor"]
if anchor:
    st.metric("最新已核验 NPM 估值 / T", anchor["value"])
    st.caption(
        f"有效日 {anchor['effective_date']} · source_id {anchor['source_id']} · "
        f"观测 {anchor['observed_at']} · 年龄 {(now - utc(anchor['observed_at'])).total_seconds() / 86400:.2f} 天"
    )
else:
    st.warning("DATA_UNAVAILABLE：没有已核验 NPM 锚点。LIVE 会报告 NO_VALID_ANCHOR。")
mode = st.radio("运行模式", ["DEMO", "LIVE"], horizontal=True)
if mode == "DEMO":
    st.warning("DEMO / SYNTHETIC：全为虚构示例，不能作为真实预测。")
if st.button("一键运行预测", type="primary", disabled=now > cfg.freeze_utc):
    with st.spinner("采集、校验、冻结输入并计算…"):
        result = forecast_once(mode=mode, engine=engine)
    if result.status == "COMPLETED":
        st.session_state["selected_run"] = result.run_id
        st.success("完成，已保存不可覆盖快照。")
    else:
        st.error(result.status)
        st.write(result.warnings)
with Session(engine) as session:
    runs = session.scalars(
        select(PredictionRunRecord).order_by(PredictionRunRecord.started_at.desc())
    ).all()
    health = session.scalars(
        select(ProviderHealth).order_by(ProviderHealth.checked_at.desc()).limit(20)
    ).all()
    settlements = session.scalars(
        select(Settlement).where(Settlement.observed_at <= now.isoformat())
    ).all()
    scores = session.scalars(select(EvaluationScore)).all() if now > cfg.freeze_utc else []
st.subheader("运行记录与封存")
if runs:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "run_id": r.run_id,
                    "mode": r.mode,
                    "status": r.status,
                    "as_of": r.as_of_utc,
                    "error": r.error_code,
                }
                for r in runs
            ]
        ),
        width="stretch",
    )
completed = [r for r in runs if r.status == "COMPLETED"]
if completed:
    ids = [r.run_id for r in completed]
    default_id = st.session_state.get("selected_run", ids[0])
    selected = st.selectbox(
        "查看封存报告", ids, index=ids.index(default_id) if default_id in ids else 0
    )
    chosen = next(r for r in completed if r.run_id == selected)
    try:
        manifest, docs = read_snapshot(Path(chosen.snapshot_path))
    except (ValueError, OSError) as error:
        st.error(f"快照校验失败：{type(error).__name__}")
        st.stop()
    st.info(
        f"当前查看：{manifest['mode']} · {manifest.get('experiment', 'LEGACY')} · {manifest['data_quality']} · {manifest['as_of_utc']}"
    )
    for warning in manifest["warnings"]:
        st.caption(warning)
    baseline, posterior = docs["baseline.json"], docs["posterior.json"]
    bins = [b.id for b in cfg.intervals]
    labels = [b.label for b in cfg.intervals]
    fig = go.Figure()
    fig.add_bar(name="先验", x=labels, y=[baseline["prior_bin_probs"][b] for b in bins])
    fig.add_bar(name="后验", x=labels, y=[posterior["bin_probabilities"][b] for b in bins])
    fig.update_layout(barmode="group", yaxis_tickformat=".0%", xaxis_title="NPM Valuation / T")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(
        pd.DataFrame(
            {
                "区间": labels,
                "先验": [baseline["prior_bin_probs"][b] for b in bins],
                "后验": [posterior["bin_probabilities"][b] for b in bins],
                "MC SE": [posterior["mc_se"][b] for b in bins],
            }
        ),
        width="stretch",
    )
    st.write(f"后验合计：{sum(posterior['bin_probabilities'].values()):.12%}")
    st.caption("MC SE 仅为模拟误差；不是预测准确率置信区间。")
    st.subheader("情景 prior → posterior")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "情景": s,
                    "先验": p,
                    "后验": posterior["scenario_posterior"][s],
                    "q05": baseline["conditional_summaries"][s]["q05"],
                    "median": baseline["conditional_summaries"][s]["median"],
                    "q95": baseline["conditional_summaries"][s]["q95"],
                }
                for s, p in baseline["scenario_prior"].items()
            ]
        ),
        width="stretch",
    )
    st.subheader("证据、重复与吸收")
    for evidence in docs["evidence.json"]:
        with st.expander(f"{evidence['cluster_id']} · {evidence['overlap_status']}"):
            st.write(
                {
                    k: evidence.get(k)
                    for k in (
                        "included",
                        "exclusion_reason",
                        "alpha",
                        "effect_channel",
                        "dedup_reason",
                        "duplicate_count",
                        "mechanism_path_ids",
                    )
                }
            )
            st.write(evidence["claim"])
            for source in evidence["sources"]:
                st.markdown(f"[{source['publisher']}]({source['canonical_url']})")
                st.caption(
                    f"公开 {source.get('published_at')} · 首次可见 {source.get('first_seen_at')}"
                )
    st.subheader("因果假设与参数敏感性")
    st.warning("causal_effect_not_identified · 全部参数为 heuristic，尚未经历史校准")
    st.code(docs["causal_graph.mmd"], language="mermaid")
    st.json(baseline["parameter_provenance"])
    st.dataframe(pd.DataFrame(docs["sensitivity.json"]).T, width="stretch")
    st.subheader("数据覆盖与审计导出")
    st.dataframe(pd.DataFrame(docs["coverage.json"]), width="stretch")
    st.download_button("下载预测报告", docs["report.md"], file_name=f"{selected}_report.md")
    st.download_button(
        "下载 manifest",
        (Path(chosen.snapshot_path) / "manifest.json").read_bytes(),
        file_name=f"{selected}_manifest.json",
    )
    st.caption(f"本地快照：{chosen.snapshot_path}")
with st.expander("数据源健康状态"):
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "provider": h.provider,
                    "status": h.status,
                    "checked_at": h.checked_at,
                    "last_success": h.last_success_at,
                    "HTTP": h.http_status,
                    "reason": h.reason,
                }
                for h in health
            ]
        ),
        width="stretch",
    )
st.subheader("结算与评分")
if now <= cfg.freeze_utc:
    st.write("尚未到结算时间。UNRESOLVED；不显示未来结算数据。")
else:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "id": s.settlement_id,
                    "status": s.status,
                    "bin": s.bin_id,
                    "effective_date": s.settlement_effective_date,
                }
                for s in settlements
            ]
        )
    )
    st.dataframe(
        pd.DataFrame(
            [
                {"run_id": s.run_id, "Brier": s.brier, "Log loss": s.log_loss, "RPS": s.rps}
                for s in scores
            ]
        )
    )
