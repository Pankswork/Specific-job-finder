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

DECISION RULES (apply in order):

1. EXPERIENCE — If description says "3+ years", "3 years exp", "senior", "lead", or clearly requires >{exp_max} years → score = 0, reasoning = "Requires >{exp_max} yr exp"

2. UNPAID — If "unpaid" appears in title or description → score = 0, reasoning = "Unpaid position"

3. INTERNSHIP — If title contains "intern" or "trainee":
   - If Remote → score normally below
   - If NOT remote and no salary mentioned → score = 0, reasoning = "Internship without salary info"
   - If salary mentioned below ₹{internship_pay}/month → score = 0

4. LOCATION — For non-internship, non-remote jobs:
   - If location is {preferred_city} → OK, score normally
   - If location is another city and salary is clearly mentioned ≥₹{relo_threshold}/month → OK (can relocate)
   - If location is another city and salary unclear or <₹{relo_threshold} → score = 0, reasoning = "Location mismatch, salary insufficient for relocation"

5. REMOTE — If Remote → always OK, score normally below

6. AI BONUS — If job involves AI/ML/LLM/AIOps/agent/automation, add +10-15 to score. Candidate has relevant AI projects (LLM cost analyzer, AIOps anomaly detection).

SCORING (0-100):
- 80+ : Strong skill match, most rules satisfied
- 50-79: Partial match, some gaps
- <50  : Poor fit

Return JSON with these exact fields:
{{"score": <0-100>, "reasoning": "<1-2 sentences explaining the score and which rules applied>", "matched_skills": ["skill1", "skill2"], "missing_skills": ["skill3", "skill4"]}}

matched_skills = skills from the profile that appear in the job title or description.
missing_skills = skills from the profile that are relevant to the role but NOT mentioned in the job description. Include at most 5.
If score is 0, matched_skills and missing_skills should be empty lists."""


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
