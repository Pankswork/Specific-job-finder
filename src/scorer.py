import json

import requests

from src.config import get_env_or_raise
from src.models import JobPost, ScoredJob

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


def _build_scoring_prompt(job: JobPost, profile: dict) -> str:
    skills_list = ", ".join(profile["skills"])
    target_roles = ", ".join(profile["target_roles"])
    locations = ", ".join(profile["preferred_locations"])
    internship_pay = profile.get("internship_monthly_pay_inr", 25000)
    relo_threshold = profile.get("relocation_salary_threshold_inr", 35000)
    preferred_city = profile.get("preferred_city", "Bangalore")
    exp_max = profile.get("experience_max_years", 2)
    auth = ", ".join(profile["work_authorization"])

    return f"""You are a job-fit evaluator. Return ONLY valid JSON. No markdown, no code fences.

PROFILE:
- Name: {profile['name']}
- Summary: {profile['summary']}
- Experience: entry-level ({profile['experience_years']} yr, max {exp_max} yrs)
- Target roles: {target_roles}
- Skills: {skills_list}
- Preferred locations: {locations}
- Preferred city: {preferred_city}
- Work authorization: {auth}
- Internship monthly pay: ₹{internship_pay}
- Relocation threshold: ₹{relo_threshold}+ monthly

JOB:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Salary info in description: {(job.description[:200] if job.description else 'N/A')}...
- Full description: {job.description[:1800]}

RULES:

1. JUNIOR-FRIENDLY — Do NOT penalize for "senior" in the description text. Only check the JOB TITLE: if the title explicitly says "Senior", "Lead", "Staff", "Principal" → score 0, reasoning "Senior-level title"

2. EXPERIENCE — Search the description for phrases like "X+ years experience" or "requires X years". If it clearly asks for 3+ years → score 0. If unclear or only 1-2 years mentioned → ignore this rule.

3. UNPAID — If "unpaid" appears in title or description → score 0

4. INTERNSHIP — If title has "intern" or "trainee" and NOT remote with no salary info → score 0

5. LOCATION — Remote jobs are always OK. Bangalore jobs are always OK. Other cities only OK if salary ≥₹{relo_threshold}/month is mentioned.

6. AI BONUS — +10 if job mentions AI/ML/LLM (candidate has AI projects)

SCORING (0-100):
Score based on: role match, skill overlap, experience fit. Be GENEROUS for entry-level.
- 0 = hard rule triggered
- 50-69 = decent match with some gaps
- 70-84 = good fit
- 85+ = strong fit with AI bonus

Return JSON:
{{"score": <0-100>, "reasoning": "<why this score>", "matched_skills": ["skill1"], "missing_skills": ["skill2"]}}

matched_skills = profile skills mentioned in job.
missing_skills = relevant profile skills NOT mentioned. Max 5.
If score=0, matched_skills and missing_skills are empty []."""


def score_job(job: JobPost, profile: dict) -> ScoredJob:
    api_key = get_env_or_raise("DEEPSEEK_API_KEY")
    prompt = _build_scoring_prompt(job, profile)

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 300,
    }

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
        return ScoredJob(
            job=job,
            score=result.get("score", 50),
            reasoning=result.get("reasoning", ""),
            matched_skills=result.get("matched_skills", []),
            missing_skills=result.get("missing_skills", []),
        )
    except Exception as e:
        return ScoredJob(
            job=job,
            score=0,
            reasoning=f"Scoring failed: {e}",
            missing_skills=[],
        )


def score_jobs(jobs: list[JobPost], profile: dict) -> list[ScoredJob]:
    return [score_job(job, profile) for job in jobs]
