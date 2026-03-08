"""ai_generation/cover_letter.py — Gemini cover letter generator."""
import re, json, time
from pathlib import Path
from typing import Dict, List

Path("outputs/cover_letters").mkdir(parents=True, exist_ok=True)


class CoverLetterGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai
        self.model  = model

    def generate(self, resume_parsed: Dict, job: Dict) -> Dict:
        prompt = f"""You are a professional cover letter writer. Write for {resume_parsed.get('experience_level','Entry Level')} candidate.

RULES: Never fabricate experience. Mirror job's exact terminology. Be specific. Under 350 words.
Return ONLY valid JSON (no markdown):
{{"cover_letter":"...","subject_line":"...","cold_email":"...","linkedin_note":"..."}}

CANDIDATE:
Name: {resume_parsed.get('name','Candidate')}
Skills: {', '.join(resume_parsed.get('skills',[])[:15])}
Level: {resume_parsed.get('experience_level','')}
Matched skills for this job: {', '.join(job.get('common_skills',[])[:8])}

JOB:
Title: {job.get('title','')}
Company: {job.get('company','')}
Description: {job.get('description','')[:1000]}"""

        try:
            model = self._genai.GenerativeModel(
                self.model,
                generation_config=self._genai.GenerationConfig(max_output_tokens=1200, temperature=0.6)
            )
            resp = model.generate_content(prompt)
            raw  = re.sub(r"```(?:json)?|```", "", resp.text).strip()
            m    = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                result = json.loads(m.group(0))
            else:
                result = {"cover_letter": raw, "subject_line": "", "cold_email": "", "linkedin_note": ""}

            # Save to file
            company = re.sub(r"[^\w]", "_", job.get("company",""))
            title   = re.sub(r"[^\w]", "_", job.get("title",""))
            fname   = f"{company}_{title}_cover.txt"
            Path(f"outputs/cover_letters/{fname}").write_text(result.get("cover_letter",""), encoding="utf-8")
            result["filename"] = fname
            return result

        except Exception as e:
            print(f"   Cover letter error: {e}")
            time.sleep(1)
            return self._fallback(resume_parsed, job)

    def generate_batch(self, resume_parsed: Dict, jobs: List[Dict], max_jobs: int = 10) -> None:
        for job in jobs[:max_jobs]:
            r = self.generate(resume_parsed, job)
            job["cover_letter"]      = r.get("cover_letter", "")
            job["cover_letter_file"] = r.get("filename", "")
            job["subject_line"]      = r.get("subject_line", "")
            job["cold_email"]        = r.get("cold_email", "")
            job["linkedin_note"]     = r.get("linkedin_note", "")
            time.sleep(0.4)

    def _fallback(self, resume: Dict, job: Dict) -> Dict:
        name    = resume.get("name", "Candidate")
        title   = job.get("title", "this role")
        company = job.get("company", "your company")
        skills  = ", ".join(job.get("common_skills", resume.get("skills", []))[:3])
        return {
            "cover_letter": (
                f"Dear Hiring Manager,\n\n"
                f"I am applying for the {title} role at {company}.\n\n"
                f"My background in {skills} aligns directly with your requirements. "
                f"I am confident I can contribute meaningfully to your team from day one.\n\n"
                f"I would welcome the opportunity to discuss how my experience fits your needs.\n\n"
                f"Best regards,\n{name}"
            ),
            "subject_line":  f"Application — {title} at {company}",
            "cold_email":    f"Hi, I saw your {title} role at {company}. My background in {skills} looks like a strong fit. Would love to connect.",
            "linkedin_note": f"Hi! I noticed the {title} opening at {company} — my background in {skills} aligns well. Would love to connect.",
            "filename": "",
        }
