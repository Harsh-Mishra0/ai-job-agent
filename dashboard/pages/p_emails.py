"""dashboard/pages/p_emails.py — Email inbox using native Streamlit only, no raw HTML cards."""
from typing import Dict
import streamlit as st
from database.db import get_responses, save_email_responses
from email_parser.gmail_parser import get_email_stats

CAT_CFG = {
    "INTERVIEW_INVITE": {"icon": "🎯", "label": "Interview Invite",  "dot": "🟢"},
    "OFFER":            {"icon": "🎉", "label": "Job Offer",         "dot": "🟡"},
    "INFO_REQUEST":     {"icon": "📋", "label": "Info Request",      "dot": "🔵"},
    "FOLLOW_UP":        {"icon": "🔔", "label": "Follow Up",         "dot": "🟠"},
    "REJECTION":        {"icon": "❌", "label": "Rejection",         "dot": "🔴"},
    "UNKNOWN":          {"icon": "📧", "label": "Other",             "dot": "⚪"},
}

ACTION_HINTS = {
    "INTERVIEW_INVITE": "📅 Reply to schedule your interview slot.",
    "OFFER":            "🎉 Review the offer letter carefully. Negotiate before signing.",
    "INFO_REQUEST":     "📎 Send the requested documents or complete any assessment.",
    "FOLLOW_UP":        "✉️ Send a polite reply to keep the conversation going.",
    "REJECTION":        "💪 Mark as closed. Consider asking for feedback.",
}


def render(user):
    uid = user["id"]
    st.markdown("## ✉️ Email Inbox Tracker")
    st.divider()

    c1, c2 = st.columns([1, 2])
    with c1:
        sync = st.button("🔄 Sync Gmail", use_container_width=True, type="primary")
    with c2:
        st.caption("Go to ⚙️ Settings → Gmail to connect your account. Demo data shown until then.")

    if sync:
        with st.spinner("Connecting to Gmail..."):
            try:
                from email_parser.gmail_parser import GmailParser
                emails = GmailParser().fetch_recruiter_emails(max_results=50)
                save_email_responses(uid, emails)
                st.success(f"✅ Synced {len(emails)} emails")
                st.rerun()
            except Exception as e:
                st.warning(f"Gmail unavailable ({e}). Loading demo data.")
                from email_parser.gmail_parser import GmailParser
                emails = GmailParser().demo_emails()
                save_email_responses(uid, emails)
                st.rerun()

    emails = get_responses(uid)
    if not emails:
        st.info("No emails yet. Click **Sync Gmail** above.")
        return

    stats = get_email_stats(emails)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total",            stats["total"])
    m2.metric("🎯 Interviews",    stats["interviews"])
    m3.metric("🎉 Offers",        stats["offers"])
    m4.metric("❌ Rejections",    stats["rejections"])
    m5.metric("⚡ Action Needed", stats["action_needed"])

    st.divider()

    label_to_cat = {v["label"]: k for k, v in CAT_CFG.items()}
    chosen_label = st.selectbox(
        "Filter", ["All"] + [v["label"] for v in CAT_CFG.values()],
        label_visibility="collapsed"
    )
    chosen_cat = label_to_cat.get(chosen_label)
    shown = [e for e in emails if not chosen_cat or e.get("category") == chosen_cat]
    st.caption(f"{len(shown)} emails")

    urgent = [e for e in shown if e.get("action_needed") and not chosen_cat]
    if urgent:
        st.markdown("### ⚡ Needs Attention")
        for e in urgent:
            _email_card(e, highlight=True)
        st.divider()
        st.markdown("### 📬 All Emails")
        shown = [e for e in shown if not e.get("action_needed")]

    for e in shown:
        _email_card(e)


def _email_card(email: Dict, highlight: bool = False):
    cat     = email.get("category", "UNKNOWN")
    cfg     = CAT_CFG.get(cat, CAT_CFG["UNKNOWN"])
    subject = str(email.get("subject") or "(no subject)")[:70]
    sender  = str(email.get("sender")  or "")
    company = str(email.get("company") or "")
    date    = str(email.get("date")    or "")[:16]
    preview = str(email.get("body_preview") or "")[:200]

    prefix  = "⚡ " if highlight else ""
    header  = f"{prefix}{cfg['icon']} {subject}"

    with st.expander(header, expanded=highlight):
        left, right = st.columns([3, 1])

        with left:
            parts = []
            if sender:  parts.append(f"📧 {sender[:55]}")
            if company: parts.append(f"🏢 {company}")
            if date:    parts.append(f"🗓 {date}")
            for p in parts:
                st.caption(p)
            if preview:
                st.markdown(f"> *{preview}...*")

        with right:
            st.markdown(f"{cfg['dot']} **{cfg['label']}**")
            if highlight:
                st.markdown("**⚡ Action needed**")

        hint = ACTION_HINTS.get(cat)
        if hint:
            st.info(hint)
