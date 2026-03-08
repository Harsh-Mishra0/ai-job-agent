"""resume_parser/parser.py — Converts PDF or text resume into structured JSON."""
import re, json, io
from pathlib import Path
from typing import Dict, List, Optional

SKILLS = {
    "pytorch","tensorflow","keras","transformers","huggingface","scikit-learn","sklearn",
    "xgboost","lightgbm","nlp","computer vision","llm","fine-tuning","mlops","mlflow",
    "wandb","faiss","langchain","onnx","deepspeed","sql","postgresql","mysql","mongodb",
    "pandas","numpy","matplotlib","plotly","spark","pyspark","kafka","airflow","dbt",
    "snowflake","bigquery","redshift","tableau","power bi","looker","excel","python",
    "java","javascript","typescript","c++","go","rust","fastapi","flask","django",
    "react","vue","docker","kubernetes","aws","gcp","azure","git","rest api","graphql",
    "linux","bash","flutter","dart","android","ios","swift","kotlin","redis","selenium",
    "playwright","statistics","r","scipy","seaborn","tensorflow","jax",
}

ROLE_PATTERNS = {
    "ML Engineer":        ["ml engineer","machine learning","mlops","ai engineer"],
    "Data Scientist":     ["data scientist","data science"],
    "Data Analyst":       ["data analyst","analytics","business analyst"],
    "NLP Engineer":       ["nlp","natural language"],
    "Software Engineer":  ["software engineer","backend","full stack","fullstack"],
    "Data Engineer":      ["data engineer","etl","pipeline"],
    "Mobile Developer":   ["flutter","android","ios","mobile"],
    "Frontend Developer": ["frontend","react","vue"],
}

EXP_LEVELS = {
    "Entry Level":  ["intern","fresher","graduate","entry","junior","0-1 year"],
    "Mid Level":    ["2 year","3 year","4 year","mid level","associate"],
    "Senior Level": ["senior","lead","principal","staff","5 year","6 year","manager"],
}


def parse_resume(source) -> Dict:
    if isinstance(source, bytes):
        text = _pdf_to_text(source)
    elif isinstance(source, str) and Path(source).exists():
        p = Path(source)
        text = _pdf_to_text(p.read_bytes()) if p.suffix == ".pdf" else p.read_text(encoding="utf-8")
    else:
        text = source or ""
    return _parse(text)


def _parse(text: str) -> Dict:
    text = re.sub(r"\r\n","\n", text)
    text = re.sub(r"\n{3,}","\n\n", text)
    text = re.sub(r"[^\x00-\x7F]"," ", text).strip()
    tl   = text.lower()
    return {
        "name":             _name(text),
        "email":            _re(r"[\w.+\-]+@[\w\-]+\.[a-z]{2,}", text),
        "phone":            _re(r"[\+\(]?[\d\s\-\(\)]{10,15}", text),
        "github":           _re(r"github\.com/[\w\-]+", tl),
        "linkedin":         _re(r"linkedin\.com/in/[\w\-]+", tl),
        "skills":           _skills(tl),
        "experience_level": _exp_level(tl),
        "roles":            _roles(tl),
        "projects":         _section_lines(text, ["projects","personal projects"]),
        "certifications":   _section_lines(text, ["certifications","certificates"]),
        "raw_text":         text,
    }


def _pdf_to_text(b: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(b)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except ImportError: pass
    try:
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(b)).pages)
    except ImportError: pass
    return ""


def _re(pattern: str, text: str) -> str:
    m = re.search(pattern, text)
    return m.group(0).strip() if m else ""


def _name(text: str) -> str:
    for line in text.split("\n")[:8]:
        line = line.strip()
        if not line or "@" in line or re.search(r"\d{5}", line): continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return line
    return ""


def _skills(tl: str) -> List[str]:
    found = []
    for s in SKILLS:
        if re.search(r"\b" + re.escape(s) + r"\b", tl):
            found.append(s)
    return sorted(set(found))


def _exp_level(tl: str) -> str:
    for level, kws in EXP_LEVELS.items():
        if any(k in tl for k in kws): return level
    yrs = re.findall(r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", tl)
    if yrs:
        mx = max(int(y) for y in yrs)
        if mx >= 5: return "Senior Level"
        if mx >= 2: return "Mid Level"
    return "Entry Level"


def _roles(tl: str) -> List[str]:
    return [r for r, pats in ROLE_PATTERNS.items() if any(p in tl for p in pats)] or ["Software Engineer"]


def _section_lines(text: str, headers: List[str]) -> List[str]:
    tl = text.lower()
    all_h = ["experience","education","projects","skills","certifications","summary","contact","objective"]
    for h in headers:
        m = re.search(r"\b" + re.escape(h) + r"\b", tl)
        if not m: continue
        start = m.end(); end = len(text)
        for oh in all_h:
            if oh in headers: continue
            nm = re.search(r"\b" + re.escape(oh) + r"\b", tl[start:])
            if nm: end = min(end, start + nm.start())
        lines = []
        for line in text[start:end].split("\n"):
            line = line.strip().lstrip("-•* ")
            if 4 < len(line) < 100: lines.append(line)
        return lines[:8]
    return []
