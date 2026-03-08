"""scraper/jobs.py — Fetch jobs from public APIs and boards."""
import re, time, hashlib, requests
from typing import List, Dict

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobAgent/1.0)"}


def _id(title: str, company: str, src: str) -> str:
    return src[:2] + "_" + hashlib.md5(f"{title}{company}".lower().encode()).hexdigest()[:10]


def fetch_all_jobs(keywords: List[str], locations: List[str]) -> List[Dict]:
    jobs, seen = [], set()
    for j in _remoteok(keywords) + _internshala(keywords):
        if j["id"] not in seen:
            seen.add(j["id"])
            jobs.append(j)
    print(f"   • Total jobs fetched: {len(jobs)}")
    return jobs


# ── RemoteOK (free public JSON API) ──────────────────────────────────────────

def _remoteok(keywords: List[str]) -> List[Dict]:
    try:
        r = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return _demo_remote()
        data = [j for j in r.json() if isinstance(j, dict) and j.get("position")]
        kw_lower = [k.lower() for k in keywords]
        results  = []
        for j in data:
            text = f"{j.get('position','')} {j.get('description','')} {' '.join(j.get('tags',[]))}".lower()
            if any(k in text for k in kw_lower):
                results.append({
                    "id":          _id(j.get("position",""), j.get("company",""), "ro"),
                    "title":       j.get("position", ""),
                    "company":     j.get("company", ""),
                    "location":    j.get("location", "Remote"),
                    "description": re.sub(r"<[^>]+>", " ", j.get("description", ""))[:2000],
                    "url":         j.get("url", ""),
                    "source":      "RemoteOK",
                    "salary":      j.get("salary", ""),
                    "tags":        j.get("tags", []),
                    "date_posted": j.get("date", ""),
                    "role_type":   "",
                    "match_score": 0.0,
                })
        print(f"   • RemoteOK: {len(results)} jobs")
        return results or _demo_remote()
    except Exception as e:
        print(f"   • RemoteOK error: {e}")
        return _demo_remote()


# ── Internshala (public listings) ────────────────────────────────────────────

def _internshala(keywords: List[str]) -> List[Dict]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("   • Internshala: bs4 not installed, using demo")
        return _demo_internshala()

    results = []
    for kw in keywords[:3]:
        try:
            url  = f"https://internshala.com/jobs/keyword-{kw.replace(' ','-')}"
            r    = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200: continue
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select(".individual_internship")[:5]:
                title   = _txt(card, ".profile")
                company = _txt(card, ".company_name")
                loc     = _txt(card, ".location_link") or "India/Remote"
                salary  = _txt(card, ".stipend")
                tags    = [s.get_text(strip=True) for s in card.select(".round_tabs span")]
                link    = card.select_one("a[href]")
                url_out = "https://internshala.com" + link["href"] if link else ""
                if title:
                    results.append({
                        "id": _id(title, company, "in"),
                        "title": title, "company": company or "Unknown",
                        "location": loc, "description": f"{title} at {company}. Skills: {', '.join(tags)}",
                        "url": url_out, "source": "Internshala", "salary": salary,
                        "tags": tags, "date_posted": "", "role_type": "", "match_score": 0.0,
                    })
            time.sleep(1)
        except Exception: continue

    print(f"   • Internshala: {len(results)} jobs")
    return results or _demo_internshala()


def _txt(card, sel: str) -> str:
    el = card.select_one(sel)
    return el.get_text(strip=True) if el else ""


# ── Demo data ─────────────────────────────────────────────────────────────────

def _demo_remote() -> List[Dict]:
    return [
        {"id":"ro_d001","title":"Machine Learning Engineer","company":"AI Startup",
         "location":"Remote","source":"RemoteOK","salary":"$80k-120k",
         "description":"Build and deploy ML models using PyTorch, Transformers, and MLflow. Work on NLP and LLM fine-tuning projects. Python required.",
         "url":"https://remoteok.com","tags":["python","pytorch","transformers","nlp","mlflow"],"date_posted":"","role_type":"","match_score":0},
        {"id":"ro_d002","title":"Data Scientist","company":"Analytics Co",
         "location":"Remote","source":"RemoteOK","salary":"$70k-100k",
         "description":"Analyze large datasets using SQL, Python, and Pandas. Build dashboards in Tableau. Work with stakeholders on KPI reporting and A/B testing.",
         "url":"https://remoteok.com","tags":["sql","python","pandas","tableau","statistics"],"date_posted":"","role_type":"","match_score":0},
        {"id":"ro_d003","title":"NLP Research Engineer","company":"DeepMind Labs",
         "location":"Remote","source":"RemoteOK","salary":"$100k-140k",
         "description":"Research and implement state-of-the-art NLP models. Fine-tune LLMs, work with FAISS for semantic search. PyTorch and Transformers required.",
         "url":"https://remoteok.com","tags":["nlp","pytorch","transformers","llm","faiss","python"],"date_posted":"","role_type":"","match_score":0},
        {"id":"ro_d004","title":"Junior Python Developer","company":"Web Agency",
         "location":"Remote","source":"RemoteOK","salary":"$40k-60k",
         "description":"Entry level Python developer. Build REST APIs with FastAPI, work with PostgreSQL. Git and Docker knowledge helpful. Mentorship provided.",
         "url":"https://remoteok.com","tags":["python","fastapi","postgresql","docker","git","rest api"],"date_posted":"","role_type":"","match_score":0},
        {"id":"ro_d005","title":"Data Analyst","company":"FinCorp",
         "location":"Remote","source":"RemoteOK","salary":"$55k-75k",
         "description":"Data analyst role. SQL, Excel, Power BI required. Work with finance team on reporting dashboards, KPI tracking, and data visualization.",
         "url":"https://remoteok.com","tags":["sql","excel","power bi","reporting","kpi"],"date_posted":"","role_type":"","match_score":0},
    ]


def _demo_internshala() -> List[Dict]:
    return [
        {"id":"in_d001","title":"Machine Learning Intern","company":"DataMind Technologies",
         "location":"Remote","source":"Internshala","salary":"₹15,000/month",
         "description":"ML internship. Python, scikit-learn, NLP knowledge required. Work on real datasets, build classifiers, assist with model evaluation.",
         "url":"https://internshala.com","tags":["python","scikit-learn","nlp","machine learning"],"date_posted":"","role_type":"","match_score":0},
        {"id":"in_d002","title":"Python Developer Intern","company":"StartupHub India",
         "location":"Bangalore/Remote","source":"Internshala","salary":"₹12,000/month",
         "description":"Python backend internship. Build REST APIs with FastAPI, PostgreSQL, write unit tests. OOP required. PPO possible.",
         "url":"https://internshala.com","tags":["python","fastapi","postgresql","rest api"],"date_posted":"","role_type":"","match_score":0},
        {"id":"in_d003","title":"Data Analyst Intern","company":"FinTech Solutions",
         "location":"Mumbai/Remote","source":"Internshala","salary":"₹10,000/month",
         "description":"SQL, Excel, Python Pandas. Build dashboards in Tableau or Power BI. Work with product and business teams on insights.",
         "url":"https://internshala.com","tags":["sql","python","pandas","tableau","excel"],"date_posted":"","role_type":"","match_score":0},
        {"id":"in_d004","title":"AI/NLP Research Intern","company":"ResearchAI Labs",
         "location":"Remote","source":"Internshala","salary":"₹20,000/month",
         "description":"NLP research. Fine-tune BERT, GPT. Text classification, named entity recognition. PyTorch required.",
         "url":"https://internshala.com","tags":["nlp","pytorch","transformers","python","bert"],"date_posted":"","role_type":"","match_score":0},
    ]
