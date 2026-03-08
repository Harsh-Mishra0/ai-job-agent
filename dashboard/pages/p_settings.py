"""dashboard/pages/p_settings.py"""
import os
import streamlit as st
from database.db import get_latest_resume, save_resume
from resume_parser.parser import parse_resume

def render(user):
    uid = user["id"]
    st.markdown("## ⚙️ Settings")
    st.divider()

    t1, t2, t3, t4, t5 = st.tabs(["🔑 Gemini API", "📱 WhatsApp", "✉️ Gmail", "📄 Resume", "⏰ Scheduler"])

    with t1:
        st.markdown("### Google Gemini (Free LLM)")
        st.markdown("Get free key → [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)")
        key = st.text_input("API Key", value=os.getenv("GEMINI_API_KEY",""), type="password", placeholder="AIza...")
        mdl = st.selectbox("Model", ["gemini-2.0-flash","gemini-2.0-flash-lite","gemini-1.5-flash","gemini-1.5-pro"])
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save", use_container_width=True):
                os.environ["GEMINI_API_KEY"] = key
                os.environ["GEMINI_MODEL"]   = mdl
                st.success("Saved for this session!")
        with c2:
            if st.button("🧪 Test", use_container_width=True):
                if not key: st.error("Enter key first.")
                else:
                    try:
                        import google.generativeai as genai
                        genai.configure(api_key=key)
                        r = genai.GenerativeModel(mdl).generate_content("Say OK in one word")
                        st.success(f"✅ {r.text.strip()[:20]}")
                    except Exception as e: st.error(f"❌ {e}")
        st.markdown("""<div class='card' style='padding:.8rem;font-size:.82rem;color:#64748b'>
            <b style='color:#94a3b8'>Colab tip:</b> Use Secrets (🔑 icon) → add <code>GEMINI_API_KEY</code>,
            then load with: <code>os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")</code>
        </div>""", unsafe_allow_html=True)

    with t2:
        st.markdown("### WhatsApp Alerts (Free)")
        method = st.radio("Method", ["CallMeBot (easier)", "Twilio Sandbox"], horizontal=True)
        if "CallMeBot" in method:
            st.markdown("""<div class='card' style='padding:.9rem'>
                <b style='color:#e2e8f0'>Setup (2 min):</b>
                <ol style='color:#94a3b8;font-size:.85rem;line-height:2'>
                <li>Add <b>+34 644 59 84 60</b> to WhatsApp contacts</li>
                <li>Send: <code>I allow callmebot to send me messages</code></li>
                <li>Get your API key from the reply</li>
                </ol></div>""", unsafe_allow_html=True)
            phone = st.text_input("Your phone (with country code)", placeholder="919876543210")
            apikey= st.text_input("CallMeBot API Key")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save", key="cb_save"):
                    os.environ["CALLMEBOT_PHONE"] = phone
                    os.environ["CALLMEBOT_KEY"]   = apikey
                    st.success("Saved!")
            with c2:
                if st.button("📱 Test", key="cb_test"):
                    from whatsapp_alert import _send_callmebot
                    ok = _send_callmebot("🤖 AI Job Agent test!", phone, apikey)
                    st.success("✅ Sent!") if ok else st.error("❌ Failed. Check phone/key.")
        else:
            sid   = st.text_input("Twilio SID",   placeholder="ACxxxxxxxx")
            token = st.text_input("Auth Token",   type="password")
            to    = st.text_input("Your WhatsApp",placeholder="whatsapp:+91...")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("💾 Save", key="tw_save"):
                    os.environ["TWILIO_SID"]   = sid
                    os.environ["TWILIO_TOKEN"] = token
                    os.environ["WHATSAPP_TO"]  = to
                    st.success("Saved!")
            with c2:
                if st.button("📱 Test", key="tw_test"):
                    from whatsapp_alert import _send_twilio
                    ok = _send_twilio("🤖 v4 test!", sid, token, "whatsapp:+14155238886", to)
                    st.success("✅ Sent!") if ok else st.error("❌ Failed.")

    with t3:
        st.markdown("### Gmail API Setup")
        st.markdown("""<div class='card' style='padding:.9rem'>
        <b style='color:#e2e8f0'>One-time setup (5 min):</b>
        <ol style='color:#94a3b8;font-size:.85rem;line-height:2.2'>
        <li>Go to <a href='https://console.cloud.google.com' target='_blank' style='color:#4f6ef7'>console.cloud.google.com</a></li>
        <li>Create project → Enable <b>Gmail API</b></li>
        <li>Credentials → OAuth 2.0 → Desktop App → Download <code>credentials.json</code></li>
        <li>Upload it below</li>
        <li>First sync opens browser for Google auth</li>
        </ol>
        <p style='color:#475569;font-size:.8rem'>Scope: gmail.readonly — read only, cannot send or delete.</p>
        </div>""", unsafe_allow_html=True)
        creds_file = st.file_uploader("Upload credentials.json", type=["json"])
        if creds_file:
            from pathlib import Path
            Path("email_parser/credentials.json").write_bytes(creds_file.read())
            st.success("✅ Saved. Go to Email Inbox → Sync Gmail to authenticate.")

    with t4:
        st.markdown("### Default Resume")
        db_r = get_latest_resume(uid)
        if db_r:
            st.success(f"✅ Saved: **{db_r['filename']}** ({len(db_r['content'])} chars)")
        up = st.file_uploader("Upload PDF", type=["pdf"])
        if up:
            raw  = up.read()
            data = parse_resume(raw)
            text = data.get("raw_text","")
            if text:
                import json
                safe = {k:v for k,v in data.items() if k!="raw_text"}
                save_resume(uid, up.name, text, json.dumps(safe))
                st.success(f"✅ Parsed! {len(data.get('skills',[]))} skills detected.")
                st.rerun()
            else:
                st.error("Could not extract text.")

    with t5:
        st.markdown("### Daily Scheduler")
        st.markdown("**Run manually:**")
        st.code("python scheduler.py", language="bash")
        st.markdown("**Cron (daily 8AM):**")
        st.code("0 8 * * * cd /path/to/ai_job_agent_final && python scheduler.py >> logs/cron.log 2>&1", language="bash")
        st.markdown("**GitHub Actions (free cloud runner):**")
        st.code("""on:
  schedule:
    - cron: '0 8 * * *'
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: python scheduler.py
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}""", language="yaml")
