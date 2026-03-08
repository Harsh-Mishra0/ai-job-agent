"""dashboard/pages/p_action_center.py
────────────────────────────────────────
Full Job Action Center — every tool you need to land the job:
  • Apply button (direct URL)
  • Resume tailoring (AI rewrites bullets for this specific role)
  • Cover letter (view, edit, download)
  • HR email finder + cold email template
  • LinkedIn networking toolkit (connection note, DM, referral ask)
  • Interview prep (predicted questions + sample answers)
  • Salary intelligence
  • Application checklist
"""

from typing import Dict, List, Optional
import streamlit as st
import re, os, time
from database.db import get_jobs, update_job_status
from confidence_explainer import explain_match

STATUS = ["Pending", "Applied", "Interviewing", "Rejected", "Offer"]

ICON  = {"ML": "🤖", "Data": "📊", "Entry-Level": "🌱"}
SCORE_COLOR = {"Strong Match": "#4ade80", "Partial Match": "#fb923c", "Weak Match": "#f87171"}
SCORE_BG    = {"Strong Match": "#052e16", "Partial Match": "#422006", "Weak Match": "#1c0505"}

# ── HR email patterns (best-guess based on company domain) ───────────────────
HR_PATTERNS = [
    "careers@{domain}", "jobs@{domain}", "hiring@{domain}",
    "hr@{domain}", "talent@{domain}", "recruiting@{domain}",
    "people@{domain}", "apply@{domain}",
]

COMMON_DOMAINS = {
    "google": "google.com", "meta": "meta.com", "amazon": "amazon.com",
    "microsoft": "microsoft.com", "apple": "apple.com", "netflix": "netflix.com",
    "openai": "openai.com", "anthropic": "anthropic.com", "cohere": "cohere.ai",
    "hugging face": "huggingface.co", "databricks": "databricks.com",
    "scale ai": "scaleai.com", "notion": "notion.so", "stripe": "stripe.com",
    "airbnb": "airbnb.com", "uber": "uber.com", "spotify": "spotify.com",
    "linkedin": "linkedin.com", "twitter": "x.com", "github": "github.com",
}

LINKEDIN_SEARCH = "https://www.linkedin.com/search/results/people/?keywords={query}&titleFilter=recruiter+OR+HR+OR+talent"
APOLLO_SEARCH   = "https://app.apollo.io/#/people?q_organization_name={company}&q_titles[]=recruiter"
HUNTER_SEARCH   = "https://hunter.io/search/{domain}"


# ─── MAIN RENDER ──────────────────────────────────────────────────────────────

def render(user):
    uid = user["id"]

    st.markdown("""
    <div style='margin-bottom:1.5rem'>
        <h2 style='margin:0'>🎯 Job Action Center</h2>
        <p style='color:#475569;margin:.3rem 0 0 0'>Every tool to apply, network, and land the job — all in one place.</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Filters ──────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([2, 1.2, 1.2, 1])
    with fc1: search   = st.text_input("🔍", placeholder="Search role, company...", label_visibility="collapsed")
    with fc2: track    = st.selectbox("Track",  ["All","ML","Data","Entry-Level"], label_visibility="collapsed")
    with fc3: status   = st.selectbox("Status", ["All"] + STATUS, label_visibility="collapsed")
    with fc4: minscore = st.number_input("Min %", 0, 100, 0, step=5, label_visibility="collapsed")

    jobs = get_jobs(uid, {k: v for k, v in {
        "search":    search    or None,
        "role_type": track     if track    != "All" else None,
        "status":    status    if status   != "All" else None,
        "min_score": minscore  if minscore > 0      else None,
    }.items() if v is not None})

    # Sort: strong first, then by score
    jobs = sorted(jobs, key=lambda j: (
        0 if j.get("match_category") == "Strong Match" else
        1 if j.get("match_category") == "Partial Match" else 2,
        -j.get("match_score", 0)
    ))

    c_total, c_strong, c_applied, c_pending = st.columns(4)
    c_total.metric("Total Jobs",    len(jobs))
    c_strong.metric("🟢 Strong",    sum(1 for j in jobs if j.get("match_category")=="Strong Match"))
    c_applied.metric("📤 Applied",  sum(1 for j in jobs if j.get("status") in ("Applied","Interviewing","Offer")))
    c_pending.metric("⏳ Pending",  sum(1 for j in jobs if j.get("status")=="Pending"))

    st.markdown(f"<p style='color:#475569;font-size:.85rem;margin-top:.5rem'><b style='color:#94a3b8'>{len(jobs)}</b> jobs found</p>", unsafe_allow_html=True)

    if not jobs:
        st.markdown("""<div class='card' style='text-align:center;padding:3rem;color:#475569'>
            <div style='font-size:2.5rem'>🎯</div>
            <p>No jobs found. Run the agent first or adjust filters.</p>
        </div>""", unsafe_allow_html=True)
        return

    # ── Job cards ─────────────────────────────────────────────────
    for job in jobs:
        _render_job_card(job, uid)


# ─── JOB CARD ─────────────────────────────────────────────────────────────────

def _render_job_card(job: Dict, uid: int):
    jid    = job["id"]
    score  = job.get("match_score", 0)
    cat    = job.get("match_category", "")
    color  = SCORE_COLOR.get(cat, "#94a3b8")
    bg     = SCORE_BG.get(cat, "#111827")
    icon   = ICON.get(job.get("role_type", ""), "💼")
    title  = job.get("title", "")
    company= job.get("company", "")
    url    = job.get("url", "")
    common = job.get("common_skills", [])
    missing= job.get("missing_skills", [])
    status = job.get("status", "Pending")

    status_color = {
        "Pending": "#64748b", "Applied": "#4f6ef7", "Interviewing": "#f59e0b",
        "Rejected": "#f87171", "Offer": "#4ade80"
    }.get(status, "#64748b")

    label = f"{icon}  **{title}**  —  {company}  |  {score:.0f}%  {cat}  |  {status}"

    with st.expander(label, expanded=False):

        # ── TOP ROW: apply button + status ────────────────────────
        top_l, top_r = st.columns([3, 1])
        with top_l:
            st.markdown(f"""
            <div style='display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;padding:.3rem 0 .6rem 0'>
                <span style='background:{bg};color:{color};padding:3px 12px;border-radius:999px;
                      font-size:12px;font-weight:700'>{score:.0f}% — {cat}</span>
                <span style='background:#1e1b4b;color:#a5b4fc;padding:2px 8px;
                      border-radius:5px;font-size:11px'>{job.get("role_type","")}</span>
                <span style='color:#475569;font-size:.83rem'>📍 {job.get("location","")[:40]}</span>
                {"<span style='color:#64748b;font-size:.82rem'>💰 "+str(job.get("salary",""))+"</span>" if job.get("salary") else ""}
                <span style='background:{status_color}22;color:{status_color};border:1px solid {status_color}44;
                      padding:2px 8px;border-radius:999px;font-size:11px'>{status}</span>
                {"<span style='background:#0c2a1a;color:#4ade80;padding:2px 7px;border-radius:4px;font-size:11px'>📄 Cover letter ready</span>" if job.get("cover_letter") else ""}
            </div>
            """, unsafe_allow_html=True)
        with top_r:
            if url and url not in ("#", ""):
                st.link_button("🚀 Apply Now", url, use_container_width=True, type="primary")
            else:
                st.markdown("<p style='color:#475569;font-size:.82rem;padding:.5rem 0'>No direct URL</p>", unsafe_allow_html=True)

        # ── MAIN TABS ─────────────────────────────────────────────
        tabs = st.tabs([
            "📋 Overview",
            "📄 Resume Builder",
            "✍️ Cover Letter",
            "📧 Find HR & Apply",
            "🤝 Networking",
            "🎤 Interview Prep",
            "💰 Salary Intel",
            "✅ Checklist",
        ])

        with tabs[0]: _tab_overview(job, uid, jid)
        with tabs[1]: _tab_resume(job, uid)
        with tabs[2]: _tab_cover_letter(job, jid)
        with tabs[3]: _tab_hr_email(job)
        with tabs[4]: _tab_networking(job)
        with tabs[5]: _tab_interview(job)
        with tabs[6]: _tab_salary(job)
        with tabs[7]: _tab_checklist(job, uid, jid)


# ─── TAB 0: OVERVIEW ──────────────────────────────────────────────────────────

def _tab_overview(job: Dict, uid: int, jid: int):
    c1, c2 = st.columns([1.5, 1])

    with c1:
        # Skills
        common  = job.get("common_skills",  [])
        missing = job.get("missing_skills", [])
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**✅ Your matched skills**")
            if common:
                st.markdown("".join(f"<span style='background:#052e16;color:#4ade80;padding:2px 8px;border-radius:4px;font-size:11px;margin:2px;display:inline-block'>{s}</span>" for s in common[:12]), unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#475569;font-size:.82rem'>None detected</p>", unsafe_allow_html=True)
        with sc2:
            st.markdown("**⚡ Skill gaps**")
            if missing:
                st.markdown("".join(f"<span style='background:#1c0505;color:#f87171;padding:2px 8px;border-radius:4px;font-size:11px;margin:2px;display:inline-block'>{s}</span>" for s in missing[:12]), unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#4ade80;font-size:.82rem'>✓ No gaps!</p>", unsafe_allow_html=True)

        if job.get("action_plan"):
            st.markdown("<br>**📋 Action Plan**", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#080d1a;border-radius:8px;padding:1rem;font-size:.82rem;color:#94a3b8;white-space:pre-line'>{job['action_plan']}</div>", unsafe_allow_html=True)

        st.markdown("<br>**📝 Job Description**", unsafe_allow_html=True)
        desc = job.get("description", "")
        st.markdown(f"<div style='background:#080d1a;border-radius:8px;padding:1rem;color:#94a3b8;font-size:.82rem;max-height:200px;overflow-y:auto;white-space:pre-wrap'>{desc[:2500]}</div>", unsafe_allow_html=True)

    with c2:
        # Confidence breakdown
        exp = explain_match(job)
        st.markdown(f"""
        <div class='card' style='padding:1rem;margin-bottom:.8rem'>
            <div style='font-size:1.3rem'>{exp['conf_emoji']}
                <span style='color:{exp["confidence_color"]};font-weight:700;margin-left:.4rem'>{exp['confidence_label']}</span>
            </div>
            <p style='color:#94a3b8;font-size:.82rem;margin:.5rem 0'>{exp['match_narrative']}</p>
        </div>""", unsafe_allow_html=True)

        for factor, vals in exp["score_breakdown"].items():
            fs = vals["score"]
            lc = {"Strong":"#4ade80","Moderate":"#fb923c","Weak":"#f87171"}.get(vals["label"],"#94a3b8")
            st.markdown(f"""<div style='margin-bottom:.6rem'>
                <div style='display:flex;justify-content:space-between;margin-bottom:2px'>
                    <span style='color:#94a3b8;font-size:.78rem'>{factor}</span>
                    <span style='color:{lc};font-size:.78rem;font-weight:600'>{fs}%</span>
                </div>
                <div style='background:#1a2540;border-radius:999px;height:5px'>
                    <div style='width:{fs}%;height:5px;border-radius:999px;background:{lc}'></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='background:#080d1a;border-left:3px solid #4f6ef7;padding:.7rem;border-radius:0 8px 8px 0;color:#94a3b8;font-size:.82rem;margin-top:.5rem'>💡 {exp['recommendation']}</div>", unsafe_allow_html=True)

        # Quick status update
        st.markdown("<br>**Update Status**", unsafe_allow_html=True)
        new_s = st.selectbox("", STATUS, index=STATUS.index(job.get("status","Pending")) if job.get("status","Pending") in STATUS else 0,
                             key=f"ov_s_{jid}", label_visibility="collapsed")
        notes = st.text_area("Notes", value=job.get("notes",""), height=60, key=f"ov_n_{jid}",
                             placeholder="Notes...", label_visibility="collapsed")
        if st.button("Save Status", key=f"ov_sv_{jid}", use_container_width=True):
            update_job_status(jid, uid, new_s, notes)
            st.success("✓ Saved"); st.rerun()


# ─── TAB 1: RESUME BUILDER ────────────────────────────────────────────────────

def _tab_resume(job: Dict, uid: int):
    st.markdown("### 📄 AI Resume Tailoring")
    st.markdown("<p style='color:#475569;font-size:.85rem'>Rewrites your resume bullets to match this specific job's language and keywords.</p>", unsafe_allow_html=True)

    from database.db import get_latest_resume
    db_resume = get_latest_resume(uid)

    if not db_resume:
        st.warning("No resume saved. Go to ⚙️ Settings → Resume to upload your PDF.")
        return

    resume_text = db_resume["content"]
    missing = job.get("missing_skills", [])
    common  = job.get("common_skills",  [])
    title   = job.get("title",  "")
    company = job.get("company","")

    # Show existing tailored resume if available
    if job.get("resume_file") and job["resume_file"] not in ("","N/A"):
        st.success(f"✅ Tailored resume already generated: `{job['resume_file']}`")

    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
        <div class='card' style='padding:1rem'>
            <div style='color:#64748b;font-size:.75rem;text-transform:uppercase;margin-bottom:.5rem'>Resume Loaded</div>
            <div style='color:#e2e8f0;font-size:.85rem'>{db_resume["filename"]}</div>
            <div style='color:#475569;font-size:.78rem'>{len(resume_text)} chars · {len(resume_text.split())} words</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='card' style='padding:1rem'>
            <div style='color:#64748b;font-size:.75rem;text-transform:uppercase;margin-bottom:.5rem'>What will be optimized</div>
            <div style='color:#94a3b8;font-size:.83rem'>
                ✓ Mirror job title: <b style='color:#e2e8f0'>{title}</b><br>
                ✓ Inject matched keywords: <b style='color:#4ade80'>{", ".join(common[:4])}</b><br>
                {"✓ Address gaps: <b style='color:#fb923c'>" + ", ".join(missing[:3]) + "</b>" if missing else "✓ No critical gaps to address"}
            </div>
        </div>""", unsafe_allow_html=True)

    with c2:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            st.warning("⚠️ Set GEMINI_API_KEY in Settings to enable AI tailoring.")

        if st.button("🤖 Generate Tailored Resume", key=f"res_{job['id']}", use_container_width=True, type="primary"):
            if not api_key:
                st.error("GEMINI_API_KEY not set. Go to ⚙️ Settings."); return
            with st.spinner("Rewriting resume for this role..."):
                result = _generate_tailored_resume(resume_text, job, api_key)
            if result:
                st.session_state[f"tailored_res_{job['id']}"] = result
                st.success("✅ Tailored resume ready!")
            else:
                st.error("Generation failed. Check your API key.")

    # Show generated resume
    tailored = st.session_state.get(f"tailored_res_{job['id']}", job.get("resume_file",""))
    if tailored and len(tailored) > 100:
        st.markdown("<br>**📄 Tailored Resume**", unsafe_allow_html=True)
        edited = st.text_area("Edit before downloading:", value=tailored, height=400,
                              key=f"res_edit_{job['id']}", label_visibility="collapsed")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("⬇️ Download .txt", edited,
                file_name=f"resume_{re.sub(r'[^\\w]','_',company)}_{re.sub(r'[^\\w]','_',title)}.txt",
                key=f"dl_res_{job['id']}", use_container_width=True)
        with c2:
            if st.button("📋 Copy to Clipboard", key=f"cp_res_{job['id']}", use_container_width=True):
                st.code(edited, language=None)
        with c3:
            st.markdown(f"**{len(edited.split())}** words", unsafe_allow_html=True)

    # Always show tips
    with st.expander("💡 ATS Optimization Tips"):
        st.markdown(f"""
        <div style='color:#94a3b8;font-size:.85rem;line-height:1.8'>
        <b style='color:#e2e8f0'>For this role at {company}:</b><br>
        • Use exact job title <b style='color:#a5b4fc'>"{title}"</b> in your headline<br>
        • Include these keywords in your bullets: <b style='color:#4ade80'>{", ".join(common[:6])}</b><br>
        {"• Try to demonstrate these even briefly: <b style='color:#fb923c'>" + ", ".join(missing[:4]) + "</b><br>" if missing else ""}
        • Quantify achievements (%, $, users, time saved)<br>
        • Keep to 1 page for entry-level, 2 for experienced<br>
        • Use standard section headers: Experience, Education, Skills, Projects<br>
        • Save as <b>PDF</b> before uploading to ATS systems
        </div>
        """, unsafe_allow_html=True)


def _generate_tailored_resume(resume_text: str, job: Dict, api_key: str) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash",
            generation_config=genai.GenerationConfig(max_output_tokens=2000, temperature=0.4))
        prompt = f"""Rewrite this resume to be perfectly tailored for the job below.

RULES:
- NEVER add fake experience, companies, or metrics
- DO mirror the job's exact terminology and keywords
- DO strengthen existing bullet points with quantification hints
- DO reorder skills section to put matched skills first
- Keep the same structure but optimize every sentence
- Output plain text, ready to copy-paste

RESUME:
{resume_text[:3000]}

JOB: {job.get('title','')} at {job.get('company','')}
DESCRIPTION: {job.get('description','')[:1500]}
KEYWORDS TO INCLUDE: {', '.join(job.get('common_skills',[])[:10])}

Output the full rewritten resume:"""
        r = model.generate_content(prompt)
        return r.text.strip()
    except Exception as e:
        print(f"Resume gen error: {e}")
        return None


# ─── TAB 2: COVER LETTER ──────────────────────────────────────────────────────

def _tab_cover_letter(job: Dict, jid: int):
    st.markdown("### ✍️ Cover Letter")
    company = job.get("company","")
    title   = job.get("title","")

    # Show existing if available
    cl = job.get("cover_letter","")

    c1, c2 = st.columns([2, 1])
    with c2:
        api_key = os.getenv("GEMINI_API_KEY","")
        if st.button("🔄 Regenerate", key=f"regen_cl_{jid}", use_container_width=True,
                     type="primary" if not cl else "secondary"):
            if not api_key:
                st.error("Set GEMINI_API_KEY in Settings."); return
            from database.db import get_latest_resume
            db_r = get_latest_resume(st.session_state.user["id"])
            if not db_r: st.error("Upload resume in Settings first."); return
            with st.spinner("Writing cover letter..."):
                result = _generate_cover_letter(db_r["content"], job, api_key)
            if result:
                st.session_state[f"cl_{jid}"] = result
                st.success("✅ Generated!")
            else:
                st.error("Generation failed.")

        if job.get("subject_line"):
            st.markdown(f"**📧 Email Subject:**")
            st.code(job["subject_line"], language=None)

    with c1:
        display_cl = st.session_state.get(f"cl_{jid}", cl)

        if display_cl:
            edited_cl = st.text_area("Cover Letter (editable):", value=display_cl, height=380,
                                     key=f"cl_edit_{jid}", label_visibility="collapsed")
            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button("⬇️ Download .txt", edited_cl,
                    file_name=f"cover_{re.sub(r'[^\\w]','_',company)}_{re.sub(r'[^\\w]','_',title)}.txt",
                    key=f"dl_cl_{jid}", use_container_width=True)
            with dl2:
                word_count = len(edited_cl.split())
                color = "#4ade80" if word_count <= 350 else "#f87171"
                st.markdown(f"<div style='text-align:center;color:{color};font-size:.85rem;padding:.5rem'>{word_count} words {'✓' if word_count<=350 else '⚠️ too long'}</div>", unsafe_allow_html=True)
        else:
            st.markdown("""<div class='card' style='padding:2rem;text-align:center;color:#475569'>
                <div style='font-size:2rem'>✍️</div>
                <p>No cover letter yet. Click Regenerate to create one with AI.</p>
            </div>""", unsafe_allow_html=True)

    # Cold email + LinkedIn note
    if job.get("cold_email") or job.get("linkedin_note"):
        st.divider()
        n1, n2 = st.columns(2)
        with n1:
            if job.get("cold_email"):
                st.markdown("**⚡ Cold Email (short version)**")
                st.markdown(f"<div style='background:#080d1a;border-left:3px solid #4f6ef7;padding:1rem;border-radius:0 8px 8px 0;color:#e2e8f0;font-size:.85rem;white-space:pre-wrap'>{job['cold_email']}</div>", unsafe_allow_html=True)
                st.download_button("⬇️ Copy Cold Email", job["cold_email"],
                    file_name="cold_email.txt", key=f"dl_ce_{jid}", use_container_width=True)
        with n2:
            if job.get("linkedin_note"):
                st.markdown("**💼 LinkedIn Connection Note**")
                chars = len(job["linkedin_note"])
                color = "#4ade80" if chars <= 300 else "#f87171"
                st.markdown(f"<div style='background:#080d1a;border-left:3px solid #0077b5;padding:1rem;border-radius:0 8px 8px 0;color:#e2e8f0;font-size:.85rem;white-space:pre-wrap'>{job['linkedin_note']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:{color};font-size:.78rem'>{chars}/300 chars</div>", unsafe_allow_html=True)


def _generate_cover_letter(resume_text: str, job: Dict, api_key: str) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash",
            generation_config=genai.GenerationConfig(max_output_tokens=1000, temperature=0.6))
        prompt = f"""Write a tailored cover letter. Rules: never fabricate, under 320 words, specific opening line about this company.

CANDIDATE RESUME:
{resume_text[:2000]}

JOB: {job.get('title','')} at {job.get('company','')}
DESCRIPTION: {job.get('description','')[:1200]}
MATCHED SKILLS: {', '.join(job.get('common_skills',[])[:8])}

Write only the cover letter text (no subject line, no JSON):"""
        r = model.generate_content(prompt)
        return r.text.strip()
    except Exception as e:
        print(f"CL gen error: {e}")
        return None


# ─── TAB 3: HR EMAIL FINDER ───────────────────────────────────────────────────

def _tab_hr_email(job: Dict):
    st.markdown("### 📧 Find HR & Apply Directly")
    company = job.get("company", "")
    title   = job.get("title", "")
    url     = job.get("url", "")

    # Guess domain
    company_lower = company.lower().strip()
    domain = COMMON_DOMAINS.get(company_lower, "")
    if not domain and company_lower:
        # Best-guess from company name
        clean  = re.sub(r"[^a-z0-9]", "", company_lower)
        domain = f"{clean}.com"

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### 🔍 HR Email Patterns")
        st.markdown(f"<p style='color:#475569;font-size:.83rem'>Likely email addresses for <b style='color:#e2e8f0'>{company}</b>:</p>", unsafe_allow_html=True)

        if domain:
            emails = [p.replace("{domain}", domain) for p in HR_PATTERNS]
            for email in emails:
                st.markdown(f"""
                <div style='background:#080d1a;border:1px solid #1a2540;border-radius:8px;
                     padding:.5rem 1rem;margin-bottom:.4rem;display:flex;align-items:center;
                     justify-content:space-between;font-size:.85rem'>
                    <span style='color:#a5b4fc;font-family:monospace'>{email}</span>
                    <span style='color:#475569;font-size:.75rem'>📋</span>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"<p style='color:#475569;font-size:.78rem;margin-top:.5rem'>ℹ️ These are patterns — verify before sending. Domain guessed as: <code>{domain}</code></p>", unsafe_allow_html=True)
        else:
            st.info("Could not guess domain. Use the search tools on the right.")

    with c2:
        st.markdown("#### 🛠️ Find Real HR Contact")

        query = f"{company} recruiter {title}"
        st.markdown(f"""
        <div style='display:flex;flex-direction:column;gap:.5rem'>
            <a href='{LINKEDIN_SEARCH.replace("{query}", query.replace(" ","+"))}' target='_blank'
               style='background:#0077b5;color:#fff;padding:.6rem 1rem;border-radius:8px;
               text-decoration:none;font-weight:600;font-size:.85rem;text-align:center'>
               🔵 Search LinkedIn Recruiters
            </a>
            <a href='{HUNTER_SEARCH.replace("{domain}", domain or company_lower+".com")}' target='_blank'
               style='background:#ff6b35;color:#fff;padding:.6rem 1rem;border-radius:8px;
               text-decoration:none;font-weight:600;font-size:.85rem;text-align:center'>
               🔎 Hunter.io Email Finder (free)
            </a>
            <a href='{APOLLO_SEARCH.replace("{company}", company.replace("","+")+".com")}' target='_blank'
               style='background:#6366f1;color:#fff;padding:.6rem 1rem;border-radius:8px;
               text-decoration:none;font-weight:600;font-size:.85rem;text-align:center'>
               🚀 Apollo.io Contact Search
            </a>
            {"<a href='" + url + "' target='_blank' style='background:linear-gradient(135deg,#4f6ef7,#7c3aed);color:#fff;padding:.6rem 1rem;border-radius:8px;text-decoration:none;font-weight:600;font-size:.85rem;text-align:center'>🌐 Official Job Posting</a>" if url and url!="#" else ""}
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 📝 Cold Email Template")

    from database.db import get_latest_resume
    try:
        db_r = get_latest_resume(st.session_state.user["id"])
        name = ""
        if db_r and db_r.get("parsed_json"):
            import json
            parsed = json.loads(db_r["parsed_json"])
            name   = parsed.get("name", "")
    except Exception:
        name = ""

    skills_str = ", ".join(job.get("common_skills", [])[:3])
    cold_email_template = f"""Subject: Application – {title} | {name or 'Your Name'}

Hi [Recruiter Name],

I came across the {title} role at {company} and wanted to reach out directly — your team's work on [specific project/product] really caught my attention.

My background in {skills_str or 'relevant technologies'} aligns closely with what you're looking for. I've [brief achievement: e.g., built X that improved Y by Z%].

I'd love to connect for even 15 minutes to learn more about the role. I've already applied via your careers page — just wanted to make a personal introduction.

Best regards,
{name or '[Your Name]'}
[LinkedIn URL] | [GitHub URL] | [Email]"""

    edited_email = st.text_area("Edit cold email:", value=cold_email_template, height=280, key=f"cold_{job['id']}", label_visibility="collapsed")
    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button("⬇️ Download Template", edited_email,
            file_name=f"cold_email_{re.sub(r'[^\\w]','_',company)}.txt",
            key=f"dl_cold_{job['id']}", use_container_width=True)
    with ec2:
        st.markdown(f"<p style='color:#475569;font-size:.82rem;padding:.4rem'>📌 Personalize [bracketed] parts before sending</p>", unsafe_allow_html=True)


# ─── TAB 4: NETWORKING ────────────────────────────────────────────────────────

def _tab_networking(job: Dict):
    st.markdown("### 🤝 Networking Toolkit")
    company = job.get("company", "")
    title   = job.get("title", "")
    skills  = ", ".join(job.get("common_skills", [])[:4])

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 💼 LinkedIn Outreach")

        conn_note = job.get("linkedin_note", "") or f"Hi! I noticed the {title} opening at {company} and my background in {skills} looks like a strong fit. Would love to connect and learn more about the team!"

        st.markdown("**Connection Request Note** (≤300 chars)")
        cn = st.text_area("", value=conn_note[:300], height=100,
                          key=f"conn_{job['id']}", label_visibility="collapsed",
                          max_chars=300, help="LinkedIn limits connection notes to 300 chars")
        st.markdown(f"<div style='color:{'#4ade80' if len(cn)<=300 else '#f87171'};font-size:.78rem'>{len(cn)}/300</div>", unsafe_allow_html=True)

        st.markdown("<br>**Direct Message (after connecting)**", unsafe_allow_html=True)
        dm = f"""Hi [Name],

Thanks for connecting! I recently applied for the {title} role at {company} and am genuinely excited about it.

I'd love to hear about your experience on the team and what makes a candidate stand out. Would you be open to a quick 10-min chat this week?

Thanks so much,
[Your Name]"""
        st.text_area("", value=dm, height=160, key=f"dm_{job['id']}", label_visibility="collapsed")

        st.markdown("<br>**Referral Request**", unsafe_allow_html=True)
        ref = f"""Hi [Name],

I hope you're doing well! I came across the {title} opening at {company} and immediately thought of your connection there.

I have {skills} experience and feel my background aligns well with the role. If you're comfortable, I'd really appreciate a referral — it would mean a lot!

I can send you my resume or any info you need. No pressure at all if it's not possible.

Thanks so much,
[Your Name]"""
        st.text_area("", value=ref, height=180, key=f"ref_{job['id']}", label_visibility="collapsed")

    with c2:
        st.markdown("#### 🔗 Find People to Reach Out To")

        links = [
            ("🔵 LinkedIn — Employees at " + company,
             f"https://www.linkedin.com/search/results/people/?keywords={company.replace(' ','+')}+engineer&facetCurrentCompany=&origin=FACETED_SEARCH"),
            ("🔵 LinkedIn — Recruiters at " + company,
             f"https://www.linkedin.com/search/results/people/?keywords={company.replace(' ','+')}+recruiter+OR+talent"),
            ("🔵 LinkedIn — {title} alumni",
             f"https://www.linkedin.com/search/results/people/?keywords={title.replace(' ','+')}+{company.replace(' ','+')}"),
            ("🐦 Twitter/X — " + company + " hiring",
             f"https://twitter.com/search?q={company.replace(' ','+')}+hiring+{title.replace(' ','+')}&src=typed_query"),
        ]

        for label, link in links:
            st.markdown(f"<a href='{link}' target='_blank' style='display:block;background:#0f1829;border:1px solid #1a2540;color:#a5b4fc;padding:.6rem 1rem;border-radius:8px;margin-bottom:.4rem;text-decoration:none;font-size:.84rem'>🔗 {label}</a>", unsafe_allow_html=True)

        st.markdown("<br>**📋 Networking Checklist**", unsafe_allow_html=True)
        steps = [
            "Find 2-3 employees at " + company + " on LinkedIn",
            "Check if any are alumni of your college",
            "Connect with personalized note (use template left)",
            "Message after they accept (use DM template)",
            "Ask for referral AFTER building rapport",
            "Follow company page to stay updated",
            "Engage with their posts (like/comment) before messaging",
        ]
        for step in steps:
            st.markdown(f"<div style='display:flex;gap:.5rem;align-items:flex-start;margin-bottom:.3rem;color:#94a3b8;font-size:.82rem'><span>□</span><span>{step}</span></div>", unsafe_allow_html=True)

        # Community links
        st.markdown("<br>**🌐 Communities to Post In**", unsafe_allow_html=True)
        communities = [
            ("r/cscareerquestions", "https://reddit.com/r/cscareerquestions"),
            ("r/MachineLearning", "https://reddit.com/r/MachineLearning"),
            ("YC Work at a Startup", "https://www.workatastartup.com"),
            ("Wellfound (AngelList)", "https://wellfound.com/jobs"),
        ]
        for name, link in communities:
            st.markdown(f"<a href='{link}' target='_blank' style='display:inline-block;background:#1a2540;color:#a5b4fc;padding:2px 10px;border-radius:5px;margin:2px;font-size:11px;text-decoration:none'>{name}</a>", unsafe_allow_html=True)


# ─── TAB 5: INTERVIEW PREP ────────────────────────────────────────────────────

def _tab_interview(job: Dict):
    st.markdown("### 🎤 Interview Prep")
    title   = job.get("title", "")
    company = job.get("company", "")
    common  = job.get("common_skills", [])
    missing = job.get("missing_skills", [])

    api_key = os.getenv("GEMINI_API_KEY","")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🤖 Generate Interview Questions", key=f"iq_{job['id']}", use_container_width=True, type="primary"):
            if not api_key:
                st.error("Set GEMINI_API_KEY in Settings."); return
            with st.spinner("Generating questions..."):
                qs = _generate_interview_questions(job, api_key)
            if qs:
                st.session_state[f"iq_{job['id']}"] = qs

    questions = st.session_state.get(f"iq_{job['id']}", "")

    if questions:
        st.markdown(questions, unsafe_allow_html=True)
    else:
        # Static fallback questions
        st.markdown("**📌 Expected Question Types**", unsafe_allow_html=True)

        sections = {
            "🧠 Technical": [
                f"Explain how you'd approach building a {common[0] if common else 'ML'} pipeline",
                f"What's the difference between {common[0] if common else 'supervised'} and {common[1] if len(common)>1 else 'unsupervised'} learning?",
                "How do you handle class imbalance in a dataset?",
                "Walk me through a project where you used " + (common[0] if common else "Python"),
                "How would you debug a model that's overfitting?",
            ],
            "🏗️ System Design": [
                f"Design an ML pipeline for {title} use case",
                "How would you scale this to handle 10M users?",
                "How do you monitor a model in production?",
            ],
            "🤝 Behavioral (STAR format)": [
                "Tell me about a time you dealt with ambiguous requirements",
                "Describe a project where you had to learn something quickly",
                "Tell me about a failure and what you learned",
                "How do you prioritize when you have multiple deadlines?",
            ],
            "🏢 Company-Specific": [
                f"Why {company} specifically?",
                f"What do you know about {company}'s products?",
                "Where do you see yourself in 3 years?",
            ],
        }

        for section, qs in sections.items():
            with st.expander(section):
                for q in qs:
                    st.markdown(f"<div style='background:#080d1a;border-left:3px solid #4f6ef7;padding:.6rem .9rem;border-radius:0 6px 6px 0;margin-bottom:.4rem;color:#e2e8f0;font-size:.84rem'>{q}</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("**📚 Resources**")
        resources = [
            ("LeetCode", "https://leetcode.com", "Coding practice"),
            ("System Design Primer", "https://github.com/donnemartin/system-design-primer", "GitHub guide"),
            ("ML Cheatsheet", "https://ml-cheatsheet.readthedocs.io", "Quick reference"),
            ("Glassdoor — " + company, f"https://www.glassdoor.com/Interview/{company.replace(' ','-')}-Interview-Questions", "Real interview Q's"),
            ("Blind — " + company, f"https://www.teamblind.com/company/{company.replace(' ','%20')}", "Employee insights"),
            ("Levels.fyi", "https://levels.fyi", "Salary + interview info"),
        ]
        for name, link, desc in resources:
            st.markdown(f"<a href='{link}' target='_blank' style='display:block;background:#0f1829;border:1px solid #1a2540;color:#a5b4fc;padding:.6rem 1rem;border-radius:8px;margin-bottom:.3rem;text-decoration:none;font-size:.83rem'>🔗 {name} <span style='color:#475569;float:right'>{desc}</span></a>", unsafe_allow_html=True)

        st.markdown("<br>**⚡ STAR Method Reminder**", unsafe_allow_html=True)
        st.markdown("""<div class='card' style='padding:.9rem;font-size:.82rem;line-height:1.9'>
            <b style='color:#4ade80'>S</b><span style='color:#94a3b8'>ituation</span> — Set the scene (1-2 sentences)<br>
            <b style='color:#60a5fa'>T</b><span style='color:#94a3b8'>ask</span> — Your specific responsibility<br>
            <b style='color:#f59e0b'>A</b><span style='color:#94a3b8'>ction</span> — Exactly what YOU did (use "I", not "we")<br>
            <b style='color:#f472b6'>R</b><span style='color:#94a3b8'>esult</span> — Quantify the outcome (%, time, $, users)
        </div>""", unsafe_allow_html=True)


def _generate_interview_questions(job: Dict, api_key: str) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash",
            generation_config=genai.GenerationConfig(max_output_tokens=1200, temperature=0.7))
        prompt = f"""Generate realistic interview questions for:
Role: {job.get('title','')} at {job.get('company','')}
Key skills: {', '.join(job.get('common_skills',[])[:8])}
Job description: {job.get('description','')[:800]}

Generate exactly:
- 4 technical questions (role-specific)
- 3 behavioral questions (STAR format)
- 2 company-specific questions
- 1 system design question

For each question, add a brief tip on how to answer. Use markdown formatting."""
        r = model.generate_content(prompt)
        return r.text.strip()
    except Exception as e:
        print(f"Interview Q gen error: {e}")
        return None


# ─── TAB 6: SALARY INTEL ──────────────────────────────────────────────────────

def _tab_salary(job: Dict):
    st.markdown("### 💰 Salary Intelligence")
    title   = job.get("title","")
    company = job.get("company","")
    loc     = job.get("location","")
    salary  = job.get("salary","")

    if salary:
        st.markdown(f"""<div style='background:#0c2a1a;border:1px solid #166534;border-radius:10px;
            padding:1rem 1.5rem;margin-bottom:1rem'>
            <div style='color:#64748b;font-size:.75rem;text-transform:uppercase'>Listed Salary</div>
            <div style='color:#4ade80;font-size:1.6rem;font-weight:800'>{salary}</div>
        </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**📊 Salary Research Links**")
        query = title.replace(" ", "+")
        comp  = company.replace(" ", "-")
        salary_links = [
            ("Levels.fyi", f"https://levels.fyi/jobs?title={query}&company={comp}",
             "Tech salaries by level"),
            ("Glassdoor Salaries", f"https://www.glassdoor.com/Salary/{comp}-{query}-Salaries",
             "Employee-reported salaries"),
            ("LinkedIn Salary", f"https://www.linkedin.com/salary/search?keywords={query}",
             "Role-based salary ranges"),
            ("PayScale", f"https://payscale.com/research/search/?job={query}",
             "Compensation by experience"),
            ("Indeed Salaries", f"https://in.indeed.com/career/{query}/salaries",
             "India-specific data"),
            ("AmbitionBox", f"https://www.ambitionbox.com/salaries/{comp}-salaries",
             "Indian companies"),
        ]
        for name, link, desc in salary_links:
            st.markdown(f"<a href='{link}' target='_blank' style='display:block;background:#0f1829;border:1px solid #1a2540;color:#a5b4fc;padding:.55rem 1rem;border-radius:8px;margin-bottom:.35rem;text-decoration:none;font-size:.83rem'>💰 {name} <span style='color:#475569;float:right;font-size:.78rem'>{desc}</span></a>", unsafe_allow_html=True)

    with c2:
        st.markdown("**🤝 Negotiation Tips**")
        tips = [
            ("Never give a number first", "Let them name the range. Say 'I'd like to understand the full package first.'"),
            ("Research before negotiating", f"Know the market rate for {title} in {loc or 'your area'} before the offer call."),
            ("Negotiate the whole package", "Base, equity, signing bonus, remote flexibility, PTO all matter."),
            ("The 24-hour rule", "Always ask for time to 'review with family' — never accept on the spot."),
            ("Counter 10-20% higher", "Most companies expect negotiation. Silence the offer, then counter."),
            ("Get everything in writing", "Verbal offers don't count. Ask for the written offer letter."),
        ]
        for tip_title, tip_body in tips:
            with st.expander(f"💡 {tip_title}"):
                st.markdown(f"<p style='color:#94a3b8;font-size:.83rem'>{tip_body}</p>", unsafe_allow_html=True)


# ─── TAB 7: CHECKLIST ─────────────────────────────────────────────────────────

def _tab_checklist(job: Dict, uid: int, jid: int):
    st.markdown("### ✅ Application Checklist")
    company = job.get("company","")
    title   = job.get("title","")
    url     = job.get("url","")
    status  = job.get("status","Pending")

    has_cl    = bool(job.get("cover_letter",""))
    has_url   = bool(url and url not in ("#",""))
    has_skills = len(job.get("common_skills",[])) > 0

    steps = [
        (True,          "✅", "Job found and matched"),
        (has_skills,    "✅" if has_skills else "⬜", "Skills analyzed"),
        (has_cl,        "✅" if has_cl else "⬜", "Cover letter generated"),
        (False,         "⬜", "Resume tailored for this role"),
        (False,         "⬜", "HR contact researched"),
        (False,         "⬜", "LinkedIn connection sent"),
        (status != "Pending", "✅" if status != "Pending" else "⬜", f"Applied ({status})"),
        (False,         "⬜", "Followed up after 1 week"),
        (status == "Interviewing", "✅" if status=="Interviewing" else "⬜", "Interview scheduled"),
        (False,         "⬜", "Thank you note sent after interview"),
        (status == "Offer", "✅" if status=="Offer" else "⬜", "Offer received"),
    ]

    completed = sum(1 for done, _, _ in steps if done)
    pct       = int(completed / len(steps) * 100)
    prog_color = "#4ade80" if pct >= 70 else "#fb923c" if pct >= 40 else "#f87171"

    st.markdown(f"""
    <div style='background:#0f1829;border:1px solid #1a2540;border-radius:10px;padding:1rem;margin-bottom:1rem'>
        <div style='display:flex;justify-content:space-between;margin-bottom:.5rem'>
            <span style='color:#94a3b8;font-size:.85rem'>Application Progress</span>
            <span style='color:{prog_color};font-weight:700'>{completed}/{len(steps)} steps · {pct}%</span>
        </div>
        <div style='background:#1a2540;border-radius:999px;height:8px'>
            <div style='width:{pct}%;height:8px;border-radius:999px;background:{prog_color};transition:width .3s'></div>
        </div>
    </div>""", unsafe_allow_html=True)

    for done, icon, label in steps:
        color = "#4ade80" if done else "#475569"
        st.markdown(f"<div style='display:flex;gap:.7rem;align-items:center;padding:.35rem 0;border-bottom:1px solid #0f1829'><span style='font-size:1rem'>{icon}</span><span style='color:{color};font-size:.85rem'>{label}</span></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick actions
    c1, c2, c3 = st.columns(3)
    with c1:
        if has_url:
            st.link_button("🚀 Apply Now", url, use_container_width=True, type="primary")
    with c2:
        new_s = st.selectbox("Update Status:", STATUS,
            index=STATUS.index(status) if status in STATUS else 0,
            key=f"ck_s_{jid}", label_visibility="collapsed")
        if st.button("Save", key=f"ck_sv_{jid}", use_container_width=True):
            update_job_status(jid, uid, new_s, "")
            st.success("✓ Updated!"); st.rerun()
    with c3:
        st.markdown(f"""<div class='card' style='padding:.7rem;text-align:center'>
            <div style='color:#64748b;font-size:.72rem'>Source</div>
            <div style='color:#a5b4fc;font-size:.82rem'>{job.get('source','')}</div>
            <div style='color:#64748b;font-size:.72rem;margin-top:.3rem'>{str(job.get('date_posted',''))[:10] or 'Recent'}</div>
        </div>""", unsafe_allow_html=True)
