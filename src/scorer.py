import re

from src.models import JobPost, ScoredJob


def _match_skills(description: str, title: str, profile_skills: list[str]) -> tuple[list[str], list[str]]:
    text = f"{(description or '')} {title}".lower()
    matched = [s for s in profile_skills if s.lower() in text]
    missing = [s for s in profile_skills if s.lower() not in text]
    return matched, missing[:5]


def _score_job(job: JobPost, profile: dict) -> tuple[int, str, list[str], list[str]]:
    title_lower = job.title.lower()
    desc_lower = (job.description or "").lower()
    title_words = set(title_lower.split())
    matched_skills, missing_skills = _match_skills(job.description, job.title, profile["skills"])

    senior_keywords = {"senior", "lead", "staff", "principal", "sr.", "sme", "expert"}
    if senior_keywords & title_words:
        return 0, "Senior-level title", [], []

    exp_matches = re.findall(r"(\d+)\s*(?:\+|-|to|–)\s*(\d+)\s*(?:years?|yrs?)", desc_lower)
    exp_matches += re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", desc_lower)
    exp_matches += re.findall(r"(?:minimum|at least|min)\s*(\d+)\s*(?:years?|yrs?)", desc_lower)
    if exp_matches:
        nums = [int(x) for m in exp_matches for x in (m if isinstance(m, tuple) else (m,))]
        max_exp = max(nums)
        if max_exp >= 3:
            return 0, f"Requires {max_exp}+ years experience", [], []

    if "unpaid" in title_lower or "unpaid" in desc_lower:
        return 0, "Unpaid position", [], []

    ai_bonus = 10 if any(w in desc_lower for w in ["ai", "ml", "llm", "machine learning", "artificial intelligence"]) else 0

    base = 50 + len(matched_skills) * 8 + ai_bonus

    loc_lower = (job.location or "").lower()
    preferred = profile.get("preferred_city", "Bangalore").lower()
    if preferred in loc_lower:
        base += 10
    if "remote" in loc_lower:
        base += 5

    score = min(base, 100)
    reasoning = f"Matched {len(matched_skills)} skills" + (f" (+{ai_bonus} AI)" if ai_bonus else "")
    return score, reasoning, matched_skills, missing_skills


def score_jobs(jobs: list[JobPost], profile: dict) -> list[ScoredJob]:
    return [ScoredJob(job=job, score=s, reasoning=r, matched_skills=m, missing_skills=miss)
            for job in jobs
            for s, r, m, miss in [_score_job(job, profile)]]
