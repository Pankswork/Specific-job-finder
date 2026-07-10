import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

REMOTEOK_API = "https://remoteok.com/api"


class RemoteOKScraper(BaseScraper):
    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        tags = self.config.get("tags", [])

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

                if tags:
                    combined = (title + " " + description).lower()
                    if not any(t.lower() in combined for t in tags):
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
        except Exception as e:
            errors.append(f"RemoteOK: {e}")

        return ScrapeResult(source="remoteok", jobs=jobs, errors=errors)
