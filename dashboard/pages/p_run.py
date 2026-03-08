"""dashboard/pages/p_run.py"""
import streamlit as st
from database.db import get_latest_resume, save_resume
from resume_parser.parser import parse_resume
from pipeline import run_pipeline
from config.settings import GEMINI_API_KEY, KEYWORDS, LOCATIONS

def render(user):
    uid = user["id"]
    st.markdown("## ▶ Run Agent")
    st.divider()

    col_cfg, col_res = st.columns(2)

    with col_cfg:
        st.markdown("### ⚙️ Settings")
        track_map    = {"All Tracks": None, "ML 🤖": "ml", "Data 📊": "data", "Entry-Level 🌱": "entry"}
        track_label  = st.selectbox("Role Track", list(track_map.keys()))
        track_filter = track_map[track_label]
        enable_llm   = st.toggle("✍️ AI Cover Letters (Gemini)", value=bool(GEMINI_API_KEY))
        if enable_llm and not GEMINI_API_KEY:
            st.warning("Set GEMINI_API_KEY in Settings first.")
            enable_llm = False
        with st.expander("🔧 Keywords & Locations"):
            kw_inp  = st.text_area("Keywords (one per line)",  "\n".join(KEYWORDS[:6]),  height=120)
            loc_inp = st.text_area("Locations (one per line)", "\n".join(LOCATIONS[:4]), height=80)
        keywords  = [k.strip() for k in kw_inp.split("\n")  if k.strip()]
        locations = [l.strip() for l in loc_inp.split("\n") if l.strip()]
        run_btn   = st.button("🚀 Run Agent", use_container_width=True, type="primary")

    with col_res:
        st.markdown("### 📄 Resume")
        tab_up, tab_txt = st.tabs(["Upload PDF", "Paste Text"])
        resume_text = ""

        with tab_up:
            pdf = st.file_uploader("PDF resume", type=["pdf"], label_visibility="collapsed")
            if pdf:
                with st.spinner("Parsing PDF..."):
                    raw  = pdf.read()
                    data = parse_resume(raw)
                    text = data.get("raw_text", "")
                if text:
                    st.session_state["resume_text"] = text
                    save_resume(uid, pdf.name, text)
                    st.success(f"✓ Parsed — {len(data.get('skills',[]))} skills found")
                    _show_parsed(data)
                    resume_text = text
                else:
                    st.error("Could not extract text. Try Paste Text.")

        with tab_txt:
            cached = st.session_state.get("resume_text", "")
            if not cached:
                db_r = get_latest_resume(uid)
                if db_r: cached = db_r["content"]
            inp = st.text_area("Paste your resume", value=cached, height=250,
                               placeholder="Paste full resume text here...",
                               label_visibility="collapsed")
            if inp.strip():
                resume_text = inp.strip()
                st.session_state["resume_text"] = resume_text

        if not resume_text:
            db_r = get_latest_resume(uid)
            if db_r:
                resume_text = db_r["content"]
                st.info(f"Using saved resume: **{db_r['filename']}**")

    if run_btn:
        if not resume_text or len(resume_text.strip()) < 30:
            st.error("❌ Upload or paste your resume first."); return

        st.divider()
        st.markdown("### 🔄 Running...")
        prog   = st.progress(0)
        status = st.empty()
        log    = st.empty()
        lines  = []

        def cb(step, total, msg):
            prog.progress(step / total)
            status.markdown(f"<p style='color:#94a3b8'>{msg}</p>", unsafe_allow_html=True)
            lines.append(f"[{step}/{total}] {msg}")
            log.code("\n".join(lines[-6:]))

        with st.spinner(""):
            result = run_pipeline(user_id=uid, resume_text=resume_text,
                                  track_filter=track_filter, keywords=keywords,
                                  locations=locations, enable_llm=enable_llm,
                                  progress_cb=cb)
        prog.progress(1.0)

        if result["success"]:
            jobs   = result["jobs"]
            strong = result["strong"]
            st.success(f"✅ Done! **{result['total']}** jobs · **{strong}** strong matches · **{result['new_jobs']}** new")
            if result.get("resume_parsed"):
                with st.expander("🧠 Resume parsed as JSON"):
                    _show_parsed(result["resume_parsed"])
            if jobs:
                st.markdown("#### 🏆 Top 5")
                ti = {"ML":"🤖","Data":"📊","Entry-Level":"🌱"}
                cc = {"Strong Match":"#4ade80","Partial Match":"#fb923c","Weak Match":"#f87171"}
                for job in jobs[:5]:
                    sc    = job.get("match_score",0)
                    color = cc.get(job.get("match_category",""),"#94a3b8")
                    st.markdown(f"""<div class='card' style='padding:.9rem;display:flex;align-items:center;gap:1rem'>
                        <span style='font-size:1.3rem'>{ti.get(job.get("role_type",""),"💼")}</span>
                        <div style='flex:1'>
                            <div style='font-weight:600;color:#e2e8f0'>{job.get("title","")}</div>
                            <div style='color:#475569;font-size:.82rem'>{job.get("company","")} · {job.get("location","")[:30]}
                            {"· 📄 Cover letter ready" if job.get("cover_letter") else ""}</div>
                        </div>
                        <span style='font-size:1.2rem;font-weight:800;color:{color}'>{sc:.0f}%</span>
                    </div>""", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📋 Job Board", use_container_width=True):
                    st.session_state.page = "jobs"; st.rerun()
            with c2:
                if st.button("📊 Analytics", use_container_width=True):
                    st.session_state.page = "analytics"; st.rerun()
        else:
            st.error(f"❌ {result.get('error','Unknown error')}")
            for e in result.get("errors",[]): st.warning(e)


def _show_parsed(data: dict):
    import json
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class='card' style='padding:.9rem'>
            <div style='color:#64748b;font-size:.72rem;text-transform:uppercase'>Candidate</div>
            <div style='color:#e2e8f0;font-weight:700'>{data.get("name","—")}</div>
            <div style='color:#94a3b8;font-size:.83rem'>{data.get("email","")}</div>
            <div style='color:#4ade80;font-weight:600;margin-top:.4rem'>{data.get("experience_level","")}</div>
            {''.join(f"<span style='background:#1e1b4b;color:#a5b4fc;padding:1px 7px;border-radius:4px;font-size:11px;margin:2px;display:inline-block'>{r}</span>" for r in data.get("roles",[]))}
        </div>""", unsafe_allow_html=True)
    with c2:
        skills = data.get("skills", [])
        if skills:
            st.markdown(f"""<div class='card' style='padding:.9rem'>
                <div style='color:#64748b;font-size:.72rem;text-transform:uppercase;margin-bottom:.4rem'>Skills ({len(skills)})</div>
                {''.join(f"<span style='background:#052e16;color:#4ade80;padding:1px 7px;border-radius:4px;font-size:11px;margin:2px;display:inline-block'>{s}</span>" for s in skills[:18])}
            </div>""", unsafe_allow_html=True)
    with st.expander("Full JSON"):
        safe = {k:v for k,v in data.items() if k!="raw_text"}
        st.code(json.dumps(safe, indent=2), language="json")
