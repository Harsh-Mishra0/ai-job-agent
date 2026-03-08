"""job_matching/matcher.py — FAISS semantic similarity matching."""
import re
from typing import List, Dict, Tuple
from resume_parser.parser import SKILLS


def rank_jobs(resume_text: str, jobs: List[Dict]) -> List[Dict]:
    """Rank jobs by similarity to resume. Uses FAISS if available, else keywords."""
    if not jobs: return jobs
    resume_skills = _extract_skills(resume_text)

    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = [f"{j.get('title','')} {j.get('description','')[:800]}" for j in jobs]
        res_emb  = model.encode([resume_text[:2000]], convert_to_numpy=True, show_progress_bar=False)
        job_embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=32)
        # Normalize
        def norm(v): n=np.linalg.norm(v,axis=-1,keepdims=True); n[n==0]=1; return v/n
        res_emb  = norm(res_emb)
        job_embs = norm(job_embs)

        try:
            import faiss
            idx = faiss.IndexFlatIP(job_embs.shape[1])
            idx.add(job_embs.astype("float32"))
            D, I = idx.search(res_emb.astype("float32"), len(jobs))
            sem_scores = {i: float(D[0][rank]) for rank, i in enumerate(I[0])}
        except ImportError:
            sims = (job_embs @ res_emb.T).flatten()
            sem_scores = {i: float(sims[i]) for i in range(len(jobs))}

        for i, job in enumerate(jobs):
            sem   = max(0.0, sem_scores.get(i, 0.0))
            skill = _skill_score(resume_skills, job)
            score = round(sem * 70 + skill * 30, 1)
            _set_score(job, score)

    except ImportError:
        for job in jobs:
            score = round(_skill_score(resume_skills, job) * 100, 1)
            _set_score(job, score)

    for job in jobs:
        common, missing = get_skill_gap(resume_skills, job)
        job["common_skills"]  = common
        job["missing_skills"] = missing

    return sorted(jobs, key=lambda j: j["match_score"], reverse=True)


def _set_score(job: Dict, score: float):
    job["match_score"]    = score
    job["match_category"] = (
        "Strong Match"  if score >= 70 else
        "Partial Match" if score >= 45 else
        "Weak Match"
    )


def _extract_skills(text: str) -> set:
    tl = text.lower()
    return {s for s in SKILLS if re.search(r"\b" + re.escape(s) + r"\b", tl)}


def _skill_score(resume_skills: set, job: Dict) -> float:
    desc = (job.get("description","") + " " + " ".join(job.get("tags",[]))).lower()
    job_skills = {s for s in SKILLS if re.search(r"\b" + re.escape(s) + r"\b", desc)}
    if not job_skills: return 0.3
    return len(resume_skills & job_skills) / len(job_skills)


def get_skill_gap(resume_skills_or_text, job: Dict) -> Tuple[List, List]:
    if isinstance(resume_skills_or_text, str):
        resume_skills = _extract_skills(resume_skills_or_text)
    else:
        resume_skills = resume_skills_or_text
    desc = (job.get("description","") + " " + " ".join(job.get("tags",[]))).lower()
    job_skills = {s for s in SKILLS if re.search(r"\b" + re.escape(s) + r"\b", desc)}
    return sorted(resume_skills & job_skills), sorted(job_skills - resume_skills)
