"""dashboard/pages/p_analytics.py"""
import streamlit as st
from database.db import get_analytics

def render(user):
    uid = user["id"]
    st.markdown("## 📊 Analytics")
    st.divider()

    a = get_analytics(uid)
    if not a["total_jobs"]:
        st.info("No data yet. Run the agent to populate analytics."); return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs",    a["total_jobs"])
    c2.metric("Total Runs",    a["total_runs"])
    c3.metric("Strong Matches", a["by_category"].get("Strong Match",{}).get("count",0))
    c4.metric("Applied",       a["by_status"].get("Applied",0))

    st.markdown("<br>", unsafe_allow_html=True)

    try:
        import plotly.graph_objects as go
        import plotly.express as px
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### By Track")
            bt = a["by_track"]
            if bt:
                fig = go.Figure(go.Pie(
                    labels=list(bt.keys()), values=list(bt.values()),
                    marker_colors=["#4f6ef7","#7c3aed","#06b6d4"],
                    hole=0.55, textinfo="label+percent",
                ))
                fig.update_layout(paper_bgcolor="#0f1829", plot_bgcolor="#0f1829",
                                   font_color="#94a3b8", showlegend=False, height=280, margin=dict(t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Match Quality")
            bc = a["by_category"]
            if bc:
                cats   = list(bc.keys())
                counts = [bc[c]["count"] for c in cats]
                colors = {"Strong Match":"#4ade80","Partial Match":"#fb923c","Weak Match":"#f87171"}
                fig = go.Figure(go.Bar(
                    x=cats, y=counts,
                    marker_color=[colors.get(c,"#4f6ef7") for c in cats],
                    text=counts, textposition="outside",
                ))
                fig.update_layout(paper_bgcolor="#0f1829", plot_bgcolor="#0f1829",
                                   font_color="#94a3b8", height=280,
                                   xaxis=dict(gridcolor="#1a2540"),
                                   yaxis=dict(gridcolor="#1a2540"), margin=dict(t=10,b=10))
                st.plotly_chart(fig, use_container_width=True)

        # Score over time
        sot = a.get("score_over_time", [])
        if len(sot) >= 2:
            st.markdown("#### Avg Match Score Over Time")
            fig = go.Figure(go.Scatter(
                x=[r["date"] for r in sot],
                y=[r["avg_score"] for r in sot],
                mode="lines+markers",
                line=dict(color="#4f6ef7", width=2),
                marker=dict(size=6, color="#4f6ef7"),
                fill="tozeroy", fillcolor="rgba(79,110,247,0.1)",
            ))
            fig.update_layout(paper_bgcolor="#0f1829", plot_bgcolor="#0f1829",
                               font_color="#94a3b8", height=240,
                               xaxis=dict(gridcolor="#1a2540"),
                               yaxis=dict(gridcolor="#1a2540", range=[0,100]), margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)

        # Application funnel
        st.markdown("#### Application Funnel")
        bs = a["by_status"]
        funnel_stages = ["Pending","Applied","Interviewing","Offer"]
        funnel_vals   = [bs.get(s, 0) for s in funnel_stages]
        if any(funnel_vals):
            fig = go.Figure(go.Funnel(
                y=funnel_stages, x=funnel_vals,
                marker=dict(color=["#475569","#4f6ef7","#7c3aed","#4ade80"]),
                textinfo="value+percent initial",
            ))
            fig.update_layout(paper_bgcolor="#0f1829", plot_bgcolor="#0f1829",
                               font_color="#94a3b8", height=260, margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        st.warning("Install plotly for charts: `pip install plotly`")
        for k, v in a.items():
            if isinstance(v, dict) and v:
                st.markdown(f"**{k}:** {v}")

    # Top companies table
    st.markdown("#### 🏆 Top 5 Matches")
    top5 = a.get("top5", [])
    if top5:
        ICON = {"ML":"🤖","Data":"📊","Entry-Level":"🌱"}
        for job in top5:
            sc = job.get("match_score",0)
            st.markdown(f"""<div class='card' style='padding:.8rem;display:flex;align-items:center;gap:1rem'>
                <span>{ICON.get(job.get("role_type",""),"💼")}</span>
                <div style='flex:1'>
                    <span style='color:#e2e8f0;font-weight:600'>{job.get("title","")}</span>
                    <span style='color:#475569'> — {job.get("company","")}</span>
                </div>
                <span style='color:{"#4ade80" if sc>=70 else "#fb923c" if sc>=45 else "#f87171"};font-weight:700'>{sc:.0f}%</span>
            </div>""", unsafe_allow_html=True)
