"""confidence_explainer.py — Match confidence breakdown."""
from typing import Dict, List


def explain_match(job: Dict) -> Dict:
    score   = job.get("match_score", 0)
    common  = job.get("common_skills", [])
    missing = job.get("missing_skills", [])

    if score >= 75:   label, color, emoji = "Excellent Match", "#22c55e", "🟢"
    elif score >= 55: label, color, emoji = "Good Match",      "#84cc16", "🟡"
    elif score >= 40: label, color, emoji = "Fair Match",      "#f59e0b", "🟠"
    else:             label, color, emoji = "Low Match",       "#ef4444", "🔴"

    skill_score = min(100, len(common) * 12)
    skill_label = "Strong" if skill_score >= 70 else "Moderate" if skill_score >= 40 else "Weak"

    breakdown = {
        "Skill Overlap":      {"score": skill_score,  "label": skill_label,
                               "detail": f"{len(common)} matched / {len(common)+len(missing)} required"},
        "Semantic Relevance": {"score": int(score),
                               "label": "Strong" if score>=70 else "Moderate" if score>=45 else "Weak",
                               "detail": "Overall resume-to-JD similarity"},
        "Tech Stack Depth":   {"score": min(100, len(common)*15),
                               "label": "Strong" if len(common)>=5 else "Moderate" if len(common)>=2 else "Weak",
                               "detail": f"{len(common)} core skills present"},
    }

    why_good  = []
    why_risky = []

    if common:
        why_good.append(f"Matched skills: {', '.join(common[:4])}")
    if score >= 70:
        why_good.append("Strong overall semantic alignment")
    if missing:
        why_risky.append(f"Missing skills: {', '.join(missing[:3])}")
    if score < 45:
        why_risky.append("Low match — heavily tailor your resume")

    if score >= 75:   rec = "Apply immediately with tailored resume."
    elif score >= 55: rec = f"Good fit. Address gaps first: {', '.join(missing[:2]) or 'none critical'}."
    elif score >= 40: rec = f"Apply selectively. Build these skills: {', '.join(missing[:2]) or 'review JD'}."
    else:             rec = "Lower priority — upskill before applying."

    company = job.get("company", "this company")
    narrative = (f"This role at {company} is a **{label}** at {score:.0f}% alignment. "
                 f"{'Strong skill coverage with ' + ', '.join(common[:3]) + '.' if common else 'Limited skill overlap detected.'} "
                 f"{'Address: ' + ', '.join(missing[:2]) + '.' if missing else 'No critical gaps found.'}")

    return {
        "confidence_label":  label,
        "confidence_color":  color,
        "conf_emoji":        emoji,
        "score_breakdown":   breakdown,
        "why_good":          why_good,
        "why_risky":         why_risky,
        "recommendation":    rec,
        "match_narrative":   narrative,
    }
