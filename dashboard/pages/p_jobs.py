"""dashboard/pages/p_jobs.py"""
from typing import Dict
import streamlit as st
from database.db import get_jobs, update_job_status
from confidence_explainer import explain_match

STATUS = ["Pending", "Applied", "Interviewing", "Rejected", "Offer"]

def render(user):
    uid = user["id"]
    st.markdown("## 📋 Job Board")
    st.divider()

    fc1, fc2, fc3, fc4 = st.columns([2, 1.2, 1.2, 1])
    with fc1: search  = st.text_input("🔍", placeholder="Search role, company...", label_visibility="collapsed")
    with fc2: track   = st.selectbox("Track",  ["All","ML","Data","Entry-Level"], label_visibility="collapsed")
    with fc3: status  = st.selectbox("Status", ["All"] + STATUS, label_visibility="collapsed")
    with fc4: minscore= st.number_input("Min %", 0, 100, 0, step=5, label_visibility="collapsed")

    jobs = get_jobs(uid, {k: v for k, v in {
        "search":    search or None,
        "role_type": track  if track  != "All" else None,
        "status":    status if status != "All" else None,
        "min_score": minscore if minscore > 0 else None,
    }.items() if v is not None})

    st.markdown(f"<p style='color:#475569;font-size:.85rem'><b style='color:#94a3b8'>{len(jobs)}</b> jobs</p>", unsafe_allow_html=True)

    if not jobs:
        st.info("No jobs found. Run the agent first or adjust filters."); return

    ICON = {"ML": "🤖", "Data": "📊", "Entry-Level": "🌱"}
    COL  = {"Strong Match": "#4ade80", "Partial Match": "#fb923c", "Weak Match": "#f87171"}
    BG   = {"Strong Match": "#052e16", "Partial Match": "#422006", "Weak Match": "#1c0505"}

    for job in jobs:
        jid    = job["id"]
        score  = job.get("match_score", 0)
        cat    = job.get("match_category", "")
        icon   = ICON.get(job.get("role_type", ""), "💼")
        color  = COL.get(cat, "#94a3b8")
        bg     = BG.get(cat, "#111827")
        common = job.get("common_skills", [])
        missing= job.get("missing_skills", [])

        with st.expander(f"{icon}  **{job.get('title','')}**  —  {job.get('company','')}   |   {score:.0f}%  {cat}"):
            c_info, c_act = st.columns([2.5, 1])

            with c_info:
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(f"""<div style='display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;padding:.3rem 0 .8rem 0'>
                        <span style='background:{bg};color:{color};padding:3px 12px;border-radius:999px;font-size:12px;font-weight:700'>{score:.0f}% — {cat}</span>
                        <span style='background:#1e1b4b;color:#a5b4fc;padding:2px 8px;border-radius:5px;font-size:11px'>{job.get("role_type","")}</span>
                        <span style='color:#475569;font-size:.83rem'>📍 {job.get("location","")[:35]}</span>
                        {"<span style='color:#64748b;font-size:.82rem'>💰 "+str(job.get("salary",""))+"</span>" if job.get("salary") else ""}
                        {"<span style='background:#0c2a1a;color:#4ade80;padding:2px 7px;border-radius:4px;font-size:11px'>📄 Cover letter</span>" if job.get("cover_letter") else ""}
                    </div>""", unsafe_allow_html=True)
                with h2:
                    url = job.get("url", "")
                    if url and url not in ("#", ""):
                        st.link_button("🔗 Apply Now", url, use_container_width=True)

                t1, t2, t3, t4, t5 = st.tabs(["Skills", "Cover Letter", "AI Pitch", "Confidence", "Description"])

                with t1:
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        st.markdown("**✅ Matched**")
                        for s in common[:10]:
                            st.markdown(f"<span style='background:#052e16;color:#4ade80;padding:2px 7px;border-radius:4px;font-size:11px;margin:2px;display:inline-block'>{s}</span>", unsafe_allow_html=True)
                    with sc2:
                        st.markdown("**⚡ Gaps**")
                        for s in missing[:10]:
                            st.markdown(f"<span style='background:#1c0505;color:#f87171;padding:2px 7px;border-radius:4px;font-size:11px;margin:2px;display:inline-block'>{s}</span>", unsafe_allow_html=True)
                    if job.get("action_plan"):
                        st.markdown("<br>**📋 Action Plan**", unsafe_allow_html=True)
                        st.markdown(f"<div style='background:#080d1a;border-radius:8px;padding:1rem;font-size:.82rem;color:#94a3b8;white-space:pre-line'>{job['action_plan']}</div>", unsafe_allow_html=True)

                with t2:
                    cl = job.get("cover_letter", "")
                    if cl:
                        st.markdown(f"<div style='background:#080d1a;border:1px solid #1a2540;border-radius:8px;padding:1.2rem;color:#e2e8f0;white-space:pre-line;line-height:1.7;font-size:.88rem'>{cl}</div>", unsafe_allow_html=True)
                        st.download_button("⬇ Download", cl, file_name=job.get("cover_letter_file","cover.txt") or "cover.txt", key=f"dl_{jid}")
                        if job.get("subject_line"):
                            st.markdown(f"**📧 Subject:** `{job['subject_line']}`")
                        if job.get("cold_email"):
                            st.markdown("**⚡ Cold Email**")
                            st.markdown(f"<div style='background:#080d1a;border-left:3px solid #4f6ef7;padding:.8rem;border-radius:0 8px 8px 0;color:#94a3b8;font-size:.84rem'>{job['cold_email']}</div>", unsafe_allow_html=True)
                        if job.get("linkedin_note"):
                            st.markdown("**💼 LinkedIn Note**")
                            st.markdown(f"<div style='background:#080d1a;border-left:3px solid #0077b5;padding:.8rem;border-radius:0 8px 8px 0;color:#94a3b8;font-size:.84rem'>{job['linkedin_note']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color:#475569'>Run agent with AI enabled to generate cover letters.</p>", unsafe_allow_html=True)

                with t3:
                    if job.get("application_pitch"):
                        st.markdown(f"<div style='background:#080d1a;border:1px solid #1a2540;border-radius:8px;padding:1rem;color:#e2e8f0;white-space:pre-line'>{job['application_pitch']}</div>", unsafe_allow_html=True)
                    if job.get("networking_message"):
                        st.markdown("**💬 LinkedIn Message**")
                        st.markdown(f"<div style='background:#080d1a;border:1px solid #1a2540;border-radius:8px;padding:1rem;color:#e2e8f0'>{job['networking_message']}</div>", unsafe_allow_html=True)

                with t4:
                    exp = explain_match(job)
                    st.markdown(f"""<div style='margin-bottom:.8rem'>
                        <span style='font-size:1.4rem'>{exp['conf_emoji']}</span>
                        <span style='color:{exp["confidence_color"]};font-size:1rem;font-weight:700;margin-left:.5rem'>{exp['confidence_label']}</span>
                    </div><p style='color:#94a3b8;font-size:.87rem'>{exp['match_narrative']}</p>""", unsafe_allow_html=True)
                    for factor, vals in exp["score_breakdown"].items():
                        fs = vals["score"]
                        lc = {"Strong":"#4ade80","Moderate":"#fb923c","Weak":"#f87171"}.get(vals["label"],"#94a3b8")
                        st.markdown(f"""<div style='margin-bottom:.7rem'>
                            <div style='display:flex;justify-content:space-between;margin-bottom:3px'>
                                <span style='color:#94a3b8;font-size:.82rem'>{factor}</span>
                                <span style='color:{lc};font-size:.82rem;font-weight:600'>{fs}% — {vals["label"]}</span>
                            </div>
                            <div style='background:#1a2540;border-radius:999px;height:6px'>
                                <div style='width:{fs}%;height:6px;border-radius:999px;background:{lc}'></div>
                            </div>
                            <div style='color:#475569;font-size:.75rem;margin-top:2px'>{vals["detail"]}</div>
                        </div>""", unsafe_allow_html=True)
                    st.markdown(f"<div style='background:#080d1a;border-left:3px solid #4f6ef7;padding:.8rem;border-radius:0 8px 8px 0;color:#94a3b8;font-size:.84rem'>💡 {exp['recommendation']}</div>", unsafe_allow_html=True)

                with t5:
                    desc = job.get("description","")
                    st.markdown(f"<div style='background:#080d1a;border-radius:8px;padding:1rem;color:#94a3b8;font-size:.82rem;max-height:260px;overflow-y:auto;white-space:pre-wrap'>{desc[:2500]}</div>", unsafe_allow_html=True)

            with c_act:
                st.markdown("**Update Status**")
                cur_s = job.get("status","Pending")
                new_s = st.selectbox("", STATUS, index=STATUS.index(cur_s) if cur_s in STATUS else 0,
                                     key=f"s_{jid}", label_visibility="collapsed")
                notes = st.text_area("Notes", value=job.get("notes",""), height=80,
                                     key=f"n_{jid}", placeholder="Notes...", label_visibility="collapsed")
                if st.button("Save", key=f"sv_{jid}", use_container_width=True):
                    update_job_status(jid, uid, new_s, notes)
                    st.success("✓"); st.rerun()
                st.markdown(f"<div style='color:#475569;font-size:.75rem;margin-top:.5rem'>📡 {job.get('source','')}</div>", unsafe_allow_html=True)
