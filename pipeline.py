"""pipeline.py — Main pipeline orchestrator."""
import os, sys, time, tempfile
from typing import Optional, List, Dict, Callable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.jobs           import fetch_all_jobs
from resume_parser.parser   import parse_resume
from job_matching.matcher   import rank_jobs, get_skill_gap
from role_classifier        import classify_job
from skill_gap              import SkillGapAnalyzer
from database.db            import create_run, finish_run, upsert_jobs
from config.settings        import GEMINI_API_KEY, KEYWORDS, LOCATIONS


def run_pipeline(
    user_id:       int,
    resume_text:   str,
    track_filter:  Optional[str]  = None,
    keywords:      Optional[List] = None,
    locations:     Optional[List] = None,
    enable_llm:    bool           = True,
    progress_cb:   Optional[Callable] = None,
) -> Dict:

    def _prog(step: int, msg: str):
        if progress_cb: progress_cb(step, 7, msg)
        else: print(f"  [{step}/7] {msg}")

    run_id = create_run(user_id, track_filter)
    errors = []

    try:
        # 1. Parse resume
        _prog(1, "📄 Parsing resume...")
        resume_parsed = parse_resume(resume_text)
        print(f"      Skills: {len(resume_parsed.get('skills',[]))} | Level: {resume_parsed.get('experience_level','')} | Roles: {resume_parsed.get('roles',['?'])}")

        # 2. Fetch jobs
        _prog(2, "🔍 Fetching jobs...")
        jobs = fetch_all_jobs(
            keywords  = keywords  or KEYWORDS,
            locations = locations or LOCATIONS,
        )

        # 3. Classify roles
        _prog(3, "🏷️ Classifying roles...")
        for job in jobs:
            job["role_type"] = classify_job(job)

        if track_filter:
            mapping = {"ml": "ML", "data": "Data", "entry": "Entry-Level"}
            target  = mapping.get(track_filter.lower())
            if target:
                jobs = [j for j in jobs if j["role_type"] == target]

        # 4. FAISS/semantic matching
        _prog(4, "🧠 Ranking by semantic similarity...")
        jobs = rank_jobs(resume_text, jobs)

        # 5. Skill gap
        _prog(5, "📊 Analyzing skill gaps...")
        analyzer = SkillGapAnalyzer(resume_text)
        for job in jobs:
            gap = analyzer.analyze(job)
            job["common_skills"]  = gap["common_skills"]
            job["missing_skills"] = gap["missing_skills"]
            job["action_plan"]    = gap["action_plan"]

        # 6. AI cover letters
        _prog(6, "✍️ Generating cover letters...")
        if enable_llm and GEMINI_API_KEY:
            try:
                from ai_generation.cover_letter import CoverLetterGenerator
                gen = CoverLetterGenerator(api_key=GEMINI_API_KEY)
                gen.generate_batch(resume_parsed, jobs[:8])
            except Exception as e:
                errors.append(f"Cover letter error: {e}")
                _set_defaults(jobs)
        else:
            _set_defaults(jobs)

        # 7. Save + alert
        _prog(7, "💾 Saving results...")
        new_jobs = upsert_jobs(user_id, run_id, jobs)
        strong   = sum(1 for j in jobs if j.get("match_category") == "Strong Match")
        finish_run(run_id, len(jobs), strong)

        try:
            from whatsapp_alert import send_whatsapp_alert
            from config.settings import WHATSAPP_TO, CALLMEBOT_PHONE
            if WHATSAPP_TO or CALLMEBOT_PHONE:
                send_whatsapp_alert(jobs[:5],
                    {"total": len(jobs), "strong": strong, "new": new_jobs},
                    user_name=resume_parsed.get("name", "Job Hunter"))
        except Exception as e:
            errors.append(f"WhatsApp: {e}")

        return {
            "success": True, "run_id": run_id,
            "jobs": jobs, "total": len(jobs),
            "new_jobs": new_jobs, "strong": strong,
            "resume_parsed": resume_parsed, "errors": errors,
        }

    except Exception as e:
        finish_run(run_id, 0, 0, status="failed")
        import traceback; traceback.print_exc()
        return {"success": False, "error": str(e), "run_id": run_id, "jobs": [], "errors": errors}


def _set_defaults(jobs: List[Dict]):
    for job in jobs:
        job.setdefault("cover_letter", "")
        job.setdefault("cover_letter_file", "")
        job.setdefault("subject_line", "")
        job.setdefault("cold_email", "")
        job.setdefault("linkedin_note", "")
        job.setdefault("application_pitch",
            f"I'm applying for the {job.get('title','')} role at {job.get('company','')}. "
            f"My skills in {', '.join(job.get('common_skills',[])[:3])} align with your requirements.")
        job.setdefault("networking_message",
            f"Hi! I noticed the {job.get('title','')} opening at {job.get('company','')} and it looks like a strong fit. Would love to connect!")
        job.setdefault("alignment_reasons", ["Skill overlap", "Domain match", "Track alignment"])
        job.setdefault("resume_file", "")
