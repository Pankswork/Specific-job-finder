from datetime import datetime

from src.config import load_seen_jobs, save_seen_jobs, append_history
from src.models import JobPost, ScoredJob


def filter_new_jobs(jobs: list[JobPost]) -> list[JobPost]:
    seen = load_seen_jobs()
    new = [j for j in jobs if j.fingerprint() not in seen]
    seen.update(j.fingerprint() for j in jobs)
    save_seen_jobs(seen)
    return new


def record_scored(jobs: list[ScoredJob]):
    entries = []
    for sj in jobs:
        entries.append({
            "fingerprint": sj.job.fingerprint(),
            "title": sj.job.title,
            "company": sj.job.company,
            "url": sj.job.url,
            "source": sj.job.source,
            "score": sj.score,
            "reasoning": sj.reasoning,
            "matched_skills": sj.matched_skills,
            "timestamp": datetime.utcnow().isoformat(),
        })
    append_history(entries)
