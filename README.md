# 🤖 AI Job Hunt Agent

> An end-to-end automated job search system built with Python, Streamlit, and Gemini AI.
> Finds jobs, matches them to your resume using semantic search, generates tailored cover letters, and tracks every application — all in one dashboard.


[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---


## ✨ What It Does

| Feature | Details |
|---|---|
| **Job Scraping** | Fetches live jobs from RemoteOK API and Internshala |
| **Semantic Matching** | Ranks jobs using FAISS vector search + sentence-transformers (all-MiniLM-L6-v2) |
| **Resume Parser** | Extracts skills, experience level, and roles from PDF or plain text |
| **AI Cover Letters** | Generates tailored cover letter, cold email, and LinkedIn note via Gemini API |
| **Role Classification** | Auto-classifies jobs into ML 🤖 / Data 📊 / Entry-Level 🌱 tracks |
| **Skill Gap Analysis** | Shows matched vs missing skills with a specific action plan per job |
| **Email Tracker** | Connects to Gmail (read-only OAuth2), classifies recruiter emails by category |
| **Networking Toolkit** | LinkedIn outreach templates, HR email finder, referral request scripts |
| **Interview Prep** | AI-generated role-specific questions with STAR-format tips |
| **Salary Intelligence** | Links to Levels.fyi, Glassdoor, AmbitionBox with negotiation scripts |
| **Application Tracker** | Kanban-style status updates with progress checklist per job |
| **WhatsApp Alerts** | Daily summary via CallMeBot (free) or Twilio |
| **Analytics Dashboard** | Plotly charts: match quality, track breakdown, score over time, application funnel |

---

## 🏗️ Architecture

```
ai_job_agent/
├── app.py                      # Streamlit entry point + auth
├── pipeline.py                 # Main orchestrator (7-step pipeline)
├── config/settings.py          # Environment config
│
├── scraper/jobs.py             # RemoteOK API + Internshala scraper
├── resume_parser/parser.py     # PDF → structured JSON (pdfplumber + regex)
├── job_matching/matcher.py     # FAISS semantic search + skill overlap scoring
├── role_classifier.py          # ML / Data / Entry-Level track classifier
├── skill_gap.py                # Skill gap analysis + action plans
├── confidence_explainer.py     # Match score breakdown engine
├── ai_generation/cover_letter.py  # Gemini API cover letter generator
├── email_parser/gmail_parser.py   # Gmail OAuth2 + email classifier
├── database/db.py              # SQLite (default) / PostgreSQL
├── whatsapp_alert.py           # CallMeBot / Twilio alerts
│
└── dashboard/pages/
    ├── p_dashboard.py          # Overview + metrics
    ├── p_run.py                # Agent runner + live progress
    ├── p_action_center.py      # Full apply toolkit (8 tabs per job)
    ├── p_jobs.py               # Filterable job board
    ├── p_emails.py             # Gmail inbox tracker
    ├── p_analytics.py          # Plotly analytics
    └── p_settings.py           # API keys + integrations
```

---

## 🧠 Technical Highlights

- **Semantic search** using FAISS `IndexFlatIP` with cosine similarity on sentence-transformer embeddings. Blended score: 70% semantic + 30% skill overlap
- **Graceful degradation** — every component has a fallback (no FAISS → numpy cosine, no Gemini → templates, no network → demo data)
- **Dual database support** — SQLite by default, auto-switches to PostgreSQL when `DATABASE_URL` is set
- **Zero hardcoded secrets** — all credentials via environment variables or Streamlit Secrets
- **Resume parser without spaCy** — pure regex + keyword taxonomy, no model download required

---

## 🚀 Quick Start

### Option A — Streamlit Cloud (recommended, no setup)
Click the **Live Demo** badge above.

### Option B — Run locally

```bash
git clone https://github.com/your-username/ai-job-agent
cd ai-job-agent
pip install -r requirements.txt
GEMINI_API_KEY=your_key streamlit run app.py
```

### Option C — Google Colab

```python
# Upload zip, then run:
import zipfile, os
with zipfile.ZipFile('ai_job_agent_final.zip') as z: z.extractall('/content/')
os.chdir('/content/ai_job_agent_final')

!pip install -q streamlit google-generativeai sentence-transformers \
             faiss-cpu pdfplumber pypdf beautifulsoup4 plotly schedule

import subprocess, threading, time
from google.colab.output import eval_js
env = {**os.environ, "PYTHONPATH": "/content/ai_job_agent_final",
       "GEMINI_API_KEY": "your_key"}
threading.Thread(target=lambda: subprocess.run(
    ["streamlit","run","app.py","--server.port","8501",
     "--server.headless","true"], env=env), daemon=True).start()
time.sleep(10)
print(eval_js("google.colab.kernel.proxyPort(8501)"))
```

---

## ⚙️ Configuration

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Free at [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `DATABASE_URL` | No | PostgreSQL URL (default: SQLite) |
| `CALLMEBOT_PHONE` | No | WhatsApp alerts via CallMeBot |
| `CALLMEBOT_KEY` | No | CallMeBot API key |
| `TWILIO_SID` | No | Twilio WhatsApp sandbox |
| `TWILIO_TOKEN` | No | Twilio auth token |

---

## 📦 Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| LLM | Google Gemini 2.0 Flash |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Search | FAISS |
| Database | SQLite / PostgreSQL |
| PDF Parsing | pdfplumber + pypdf |
| Web Scraping | requests + BeautifulSoup4 |
| Charts | Plotly |
| Email | Gmail API (OAuth2) |
| Alerts | CallMeBot / Twilio |

---

## 🗺️ Roadmap

- [ ] LinkedIn job scraper (when API access available)
- [ ] Resume PDF export with formatting
- [ ] Multi-user admin dashboard
- [ ] Automated follow-up email scheduler
- [ ] Job market trend analysis

---

## 👤 Author

Built by **[Harsh Mishra]** — [LinkedIn](https://linkedin.com/in/harshmishra04)
---

## 📄 License

MIT — free to use, modify, and share.
