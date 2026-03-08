"""role_classifier.py — Classify jobs into ML / Data / Entry-Level tracks."""
from typing import Dict

ML_STRONG    = ["pytorch","transformers","fine-tuning","llm","nlp","computer vision",
                "mlops","mlflow","wandb","onnx","deepspeed","rlhf","embeddings",
                "model deployment","feature engineering","ml pipeline","vector database"]
ML_SOFT      = ["machine learning","deep learning","neural network","scikit-learn",
                "xgboost","model training","inference","research engineer","ai engineer",
                "ml engineer","predictive model"]
DATA_STRONG  = ["sql","power bi","tableau","looker","kpi","dashboard","reporting",
                "data warehouse","dbt","snowflake","bigquery","redshift","analytics engineer",
                "data analyst","data scientist","business intelligence","etl","data pipeline",
                "product analytics","data science","a/b testing","cohort analysis"]
DATA_SOFT    = ["excel","metrics","data visualization","stakeholder","pandas","statistics",
                "statistical analysis","numpy","seaborn"]
ENTRY_STRONG = ["intern","internship","junior developer","junior engineer","graduate trainee",
                "new graduate","entry level","entry-level","associate engineer","junior python"]
ENTRY_SOFT   = ["0-2 years","recent graduate","no experience","will train","mentorship"]
SENIOR_GUARD = ["senior","staff","principal","lead","manager","director","head of",
                "architect","5+ years","6+ years","7+ years"]

EMPHASIS = {
    "ML":          {"highlight_keywords":["pytorch","transformers","nlp","llm","mlops"],
                    "de_emphasize":["excel","reporting","dashboards"],
                    "pitch_tone":"confident and technically precise",
                    "opening_frame":"an ML/AI engineer"},
    "Data":        {"highlight_keywords":["sql","tableau","kpi","analytics","dbt"],
                    "de_emphasize":["pytorch","fine-tuning","rlhf"],
                    "pitch_tone":"data-driven and business-focused",
                    "opening_frame":"a data analyst/scientist"},
    "Entry-Level": {"highlight_keywords":["python","rest api","git","docker","sql"],
                    "de_emphasize":["lead","architect","senior"],
                    "pitch_tone":"enthusiastic and eager to learn",
                    "opening_frame":"an early-career engineer"},
}


def _score(text: str, keywords: list, weight: float = 1.0) -> float:
    tl = text.lower()
    return sum(weight for k in keywords if k in tl)

def classify_job(job: Dict) -> str:
    text  = f"{job.get('title','')} {job.get('description','')} {' '.join(job.get('tags',[]))}"
    tl    = text.lower()
    is_senior = any(s in tl for s in SENIOR_GUARD)

    ml_score    = _score(tl, ML_STRONG, 2.0)    + _score(tl, ML_SOFT, 1.0)
    data_score  = _score(tl, DATA_STRONG, 2.0)  + _score(tl, DATA_SOFT, 1.0)
    entry_score = _score(tl, ENTRY_STRONG, 2.0) + _score(tl, ENTRY_SOFT, 1.0)

    if is_senior: entry_score = 0

    best = max(ml_score, data_score, entry_score)
    if best == 0:           return "ML"
    if best == entry_score: return "Entry-Level"
    if best == data_score:  return "Data"
    return "ML"

def get_resume_emphasis(role_type: str) -> Dict:
    return EMPHASIS.get(role_type, EMPHASIS["ML"])
