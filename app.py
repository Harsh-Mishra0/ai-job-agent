"""app.py — AI Job Agent v4 — Main entry point. Run: streamlit run app.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_user, create_user

st.set_page_config(page_title="AI Job Agent v4", page_icon="🤖",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.stApp{background:#080d1a;color:#e2e8f0;}
[data-testid="stSidebar"]{background:#0c1221!important;border-right:1px solid #1a2540;}
[data-testid="stSidebar"] *{color:#7c8db5!important;}
.card{background:#0f1829;border:1px solid #1a2540;border-radius:12px;padding:1.2rem;margin-bottom:.8rem;}
.stButton>button{background:linear-gradient(135deg,#4f6ef7,#7c3aed)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-weight:600!important;}
.stTabs [data-baseweb="tab-list"]{background:#0f1829;border-radius:10px;padding:3px;border:1px solid #1a2540;}
.stTabs [aria-selected="true"]{background:#1a2540!important;color:#e2e8f0!important;}
[data-testid="metric-container"]{background:#0f1829;border:1px solid #1a2540;border-radius:10px;padding:.8rem;}
[data-testid="metric-container"] label{color:#475569!important;font-size:11px!important;text-transform:uppercase;}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#e2e8f0!important;font-size:1.8rem!important;font-weight:700!important;}
h1,h2,h3{color:#f1f5f9!important;}
.stTextInput input,.stTextArea textarea{background:#0f1829!important;border:1px solid #1a2540!important;border-radius:8px!important;color:#e2e8f0!important;}
hr{border-color:#1a2540!important;}
::-webkit-scrollbar{width:5px;} ::-webkit-scrollbar-thumb{background:#1a2540;border-radius:3px;}
</style>""", unsafe_allow_html=True)

init_db()

if "user" not in st.session_state: st.session_state.user = None
if "page" not in st.session_state: st.session_state.page = "login"


def show_auth():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""<div style='text-align:center;margin-bottom:2rem'>
            <div style='font-size:3rem'>🤖</div>
            <h1 style='font-size:1.9rem;font-weight:800;background:linear-gradient(135deg,#4f6ef7,#a855f7);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent'>AI Job Hunt Agent v4</h1>
            <p style='color:#3d5a80;font-size:.9rem'>Resume Intelligence · FAISS Matching · Cover Letters · Email Tracker</p>
        </div>""", unsafe_allow_html=True)

        t1, t2 = st.tabs(["Sign In", "Create Account"])
        with t1:
            with st.form("login"):
                u = st.text_input("Username or Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    user = verify_user(u, p)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
        with t2:
            with st.form("signup"):
                nu = st.text_input("Username")
                ne = st.text_input("Email")
                np_ = st.text_input("Password", type="password")
                nc = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not all([nu, ne, np_]): st.error("All fields required.")
                    elif np_ != nc:            st.error("Passwords don't match.")
                    elif len(np_) < 6:         st.error("Min 6 characters.")
                    else:
                        uid = create_user(nu, ne, np_)
                        if uid:
                            st.session_state.user = verify_user(nu, np_)
                            st.session_state.page = "dashboard"
                            st.rerun()
                        else:
                            st.error("Username or email already taken.")


def show_app():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"""<div style='padding:.8rem 0;border-bottom:1px solid #1a2540;margin-bottom:1rem'>
            <div style='font-size:1.4rem'>🤖</div>
            <div style='font-weight:700;color:#e2e8f0'>AI Job Agent v4</div>
            <div style='color:#3d5a80;font-size:.75rem'>👤 {user['username']}</div>
        </div>""", unsafe_allow_html=True)

        nav = {"🏠 Dashboard": "dashboard", "▶ Run Agent": "run",
               "🎯 Action Center": "actions", "📋 Job Board": "jobs",
               "✉️ Email Inbox": "emails",
               "📊 Analytics": "analytics", "⚙️ Settings": "settings"}
        for label, key in nav.items():
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state.page == key else "secondary"):
                st.session_state.page = key; st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.user = None; st.session_state.page = "login"; st.rerun()

    pg = st.session_state.page
    if   pg == "dashboard": from dashboard.pages.p_dashboard import render; render(user)
    elif pg == "run":        from dashboard.pages.p_run       import render; render(user)
    elif pg == "actions":    from dashboard.pages.p_action_center import render; render(user)
    elif pg == "jobs":       from dashboard.pages.p_jobs      import render; render(user)
    elif pg == "emails":     from dashboard.pages.p_emails    import render; render(user)
    elif pg == "analytics":  from dashboard.pages.p_analytics import render; render(user)
    elif pg == "settings":   from dashboard.pages.p_settings  import render; render(user)


if st.session_state.user is None:
    show_auth()
else:
    show_app()
