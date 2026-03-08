"""dashboard/pages/p_dashboard.py"""
import streamlit as st
from database.db import get_analytics, get_jobs, get_runs

def render(user):
    uid = user["id"]
    st.markdown("## 🏠 Dashboard")
    st.divider()

    analytics = get_analytics(uid)
    total     = analytics.get("total_jobs", 0)
    runs      = analytics.get("total_runs", 0)
    by_cat    = analytics.get("by_category", {})
    strong    = by_cat.get("Strong Match",  {}).get("count", 0)
    partial   = by_cat.get("Partial Match", {}).get("count", 0)
    by_status = analytics.get("by_status", {})
    applied   = by_status.get("Applied", 0) + by_status.get("Interviewing", 0) + by_status.get("Offer", 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs",      total)
    c2.metric("🟢 Strong Matches", strong)
    c3.metric("🟠 Partial Matches", partial)
    c4.metric("📤 Applied",        applied)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.markdown("### 🏆 Top Matches")
        top5 = analytics.get("top5", [])
        if top5:
            ti = {"ML": "🤖", "Data": "📊", "Entry-Level": "🌱"}
            cc = {"Strong Match": "#4ade80", "Partial Match": "#fb923c", "Weak Match": "#f87171"}
            jobs = get_jobs(uid, {"limit": 5})
            for job in jobs:
                score = job.get("match_score", 0)
                cat   = job.get("match_category", "")
                color = cc.get(cat, "#94a3b8")
                icon  = ti.get(job.get("role_type", ""), "💼")
                st.markdown(f"""
                <div class='card' style='padding:.9rem;display:flex;align-items:center;gap:1rem'>
                    <span style='font-size:1.4rem'>{icon}</span>
                    <div style='flex:1'>
                        <div style='font-weight:600;color:#e2e8f0'>{job.get("title","")}</div>
                        <div style='color:#475569;font-size:.83rem'>{job.get("company","")} · {job.get("location","")[:30]}</div>
                    </div>
                    <span style='font-size:1.3rem;font-weight:800;color:{color}'>{score:.0f}%</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Run the agent to see top matches here.")

    with col_right:
        st.markdown("### 📊 Breakdown")
        by_track = analytics.get("by_track", {})
        if by_track:
            for track, count in by_track.items():
                icon = {"ML": "🤖", "Data": "📊", "Entry-Level": "🌱"}.get(track, "💼")
                pct  = int(count / max(total, 1) * 100)
                st.markdown(f"""
                <div style='margin-bottom:.6rem'>
                    <div style='display:flex;justify-content:space-between;font-size:.83rem;margin-bottom:3px'>
                        <span style='color:#94a3b8'>{icon} {track}</span>
                        <span style='color:#64748b'>{count} ({pct}%)</span>
                    </div>
                    <div style='background:#1a2540;border-radius:999px;height:6px'>
                        <div style='width:{pct}%;height:6px;border-radius:999px;background:linear-gradient(90deg,#4f6ef7,#7c3aed)'></div>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("### 📋 Status")
        status_icons = {"Pending":"⏳","Applied":"📤","Interviewing":"🎯","Rejected":"❌","Offer":"🎉"}
        if by_status:
            for s, cnt in by_status.items():
                st.markdown(f"<div style='display:flex;justify-content:space-between;color:#94a3b8;font-size:.85rem;padding:.2rem 0'>"
                            f"<span>{status_icons.get(s,'•')} {s}</span><span style='color:#e2e8f0;font-weight:600'>{cnt}</span></div>",
                            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🕐 Recent Runs")
    recent_runs = get_runs(uid, limit=5)
    if recent_runs:
        for r in recent_runs:
            st.markdown(f"""<div class='card' style='padding:.8rem;display:flex;gap:1.5rem;align-items:center'>
                <span style='color:{"#4ade80" if r.get("status")=="completed" else "#f87171"}'>{"✅" if r.get("status")=="completed" else "❌"}</span>
                <span style='color:#94a3b8;font-size:.85rem;flex:1'>{str(r.get("run_at",""))[:16]}</span>
                <span style='color:#64748b;font-size:.83rem'>Found: {r.get("jobs_found",0)} · Strong: {r.get("jobs_matched",0)}</span>
                {"<span style='background:#1e1b4b;color:#a5b4fc;padding:1px 8px;border-radius:5px;font-size:11px'>" + r.get("track_filter","All") + "</span>" if r.get("track_filter") else ""}
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No runs yet. Go to Run Agent to start.")

    if st.button("▶ Run Agent Now", type="primary"):
        st.session_state.page = "run"; st.rerun()
