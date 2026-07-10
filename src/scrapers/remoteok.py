import re

import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

REMOTEOK_API = "https://remoteok.com/api"

TITLE_KEYWORDS = [
    "devops", "sre", "site reliability", "platform engineer",
    "cloud engineer", "cloud intern", "devsecops",
    "infrastructure engineer", "aws engineer", "aws intern",
    "kubernetes engineer", "k8s", "terraform",
    "release engineer", "ci/cd", "backend engineer",
]

EXCLUDE_KEYWORDS = [
    "teacher", "professor", "profesor", "docente", "instructor",
    "social media", "marketing", "hr ", "human resource",
    "houseperson", "housekeeper", "attractions",
    "content creator", "creative strategist",
    "architectural", "drafter", "data entry",
    "administrative assistant", "executive assistant",
    "customer support", "customer service",
    "project coordinator", "events manager",
    "accounts assistant", "accountant", "finance",
    "recruiter", "hiring", "sales",
    "nurse", "doctor", "medical",
    "driver", "delivery", "cleaner",
    "legal", "lawyer", "paralegal",
    "writer", "editor", "translator",
    "designer", "photographer", "videographer",
]


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    if any(excl in title_lower for excl in EXCLUDE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in TITLE_KEYWORDS)


class RemoteOKScraper(BaseScraper):
    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        max_jobs = self.config.get("max_jobs", 30)

        try:
            resp = requests.get(
                REMOTEOK_API,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

            raw_jobs = data[1:] if isinstance(data, list) and len(data) > 1 else data
            for item in raw_jobs:
                if not isinstance(item, dict):
                    continue
                title = (item.get("position") or "").strip()
                company = (item.get("company") or "").strip()
                url = (item.get("url") or "").strip()
                description = (item.get("description") or "").strip()
                location = (item.get("location") or "Remote").strip()
                salary = item.get("salary") or None
                date_str = item.get("date") or None

                if not title or not url:
                    continue

                if not _is_relevant(title):
                    continue

                jobs.append(JobPost(
                    title=title,
                    company=company or "Unknown",
                    location=location,
                    url=url,
                    source="remoteok",
                    description=description,
                    salary=salary,
                    posted_date=date_str,
                ))

                if len(jobs) >= max_jobs:
                    break
        except Exception as e:
            errors.append(f"RemoteOK: {e}")

        return ScrapeResult(source="remoteok", jobs=jobs, errors=errors)
