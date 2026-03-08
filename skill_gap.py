"""skill_gap.py — Skill gap analysis with action plans."""
import re
from typing import Dict, List
from role_classifier import get_resume_emphasis
from resume_parser.parser import SKILLS

ACTIONS = {
    "pytorch":       "Build a CNN classifier on MNIST with PyTorch",
    "transformers":  "Fine-tune BERT on a text classification dataset (HuggingFace)",
    "sql":           "Complete SQLZoo or Mode Analytics SQL tutorial",
    "docker":        "Dockerize a Flask app and push to Docker Hub",
    "aws":           "Deploy a Lambda function + S3 bucket on AWS free tier",
    "tableau":       "Build a sales dashboard on Tableau Public with sample data",
    "power bi":      "Create a KPI report in Power BI Desktop (free)",
    "spark":         "Run a PySpark job locally on a CSV dataset",
    "dbt":           "Complete dbt Learn fundamentals course (free)",
    "fastapi":       "Build a REST API with FastAPI + automatic Swagger docs",
    "kubernetes":    "Deploy a containerized app on Minikube locally",
    "mlflow":        "Track a scikit-learn experiment with MLflow locally",
    "flutter":       "Build a Flutter todo app with Firebase backend",
    "react":         "Build a React dashboard with mock API data",
    "nlp":           "Build a sentiment classifier using HuggingFace pipeline",
    "llm":           "Build a RAG chatbot with LangChain + free Gemini API",
}

DEFAULT_ACTION = "Take a free course on Coursera or build a project on GitHub"


class SkillGapAnalyzer:
    def __init__(self, resume_text: str = ""):
        self.resume_text   = resume_text
        self.resume_skills = self._extract_skills(resume_text)

    def _extract_skills(self, text: str) -> set:
        tl = text.lower()
        return {s for s in SKILLS if re.search(r"\b" + re.escape(s) + r"\b", tl)}

    def analyze(self, job: Dict) -> Dict:
        desc_lower = (job.get("description","") + " " + " ".join(job.get("tags",[]))).lower()
        job_skills  = {s for s in SKILLS if re.search(r"\b" + re.escape(s) + r"\b", desc_lower)}
        common   = sorted(self.resume_skills & job_skills)
        missing  = sorted(job_skills - self.resume_skills)
        plan     = self._build_plan(missing, job.get("role_type","ML"))
        return {
            "common_skills":  common,
            "missing_skills": missing,
            "action_plan":    plan,
        }

    def _build_plan(self, missing: List[str], role_type: str) -> str:
        if not missing: return "You meet all detected skill requirements. Focus on tailoring your language."
        lines = [f"Top skills to develop for {role_type} roles:\n"]
        for skill in missing[:5]:
            action = ACTIONS.get(skill, DEFAULT_ACTION)
            lines.append(f"• [{skill.upper()}] {action}")
        return "\n".join(lines)
