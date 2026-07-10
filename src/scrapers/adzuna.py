import os

import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs/in/search/1"


class AdzunaScraper(BaseScraper):
    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        cfg = self.config
        app_id = cfg.get("app_id") or os.environ.get("ADZUNA_APP_ID", "")
        app_key = cfg.get("app_key") or os.environ.get("ADZUNA_API_KEY", "")
        query = cfg.get("query", "devops")
        where = cfg.get("where", "India")
        max_jobs = cfg.get("max_jobs", 20)

        if not app_id or not app_key:
            errors.append("adzuna: missing app_id or app_key")
            return ScrapeResult(source="adzuna", jobs=jobs, errors=errors)

        try:
            resp = requests.get(
                ADZUNA_BASE,
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": query,
                    "where": where,
                    "results_per_page": max_jobs,
                    "content-type": "application/json",
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("results", []):
                title = (item.get("title") or "").strip()
                company = item.get("company", {}).get("display_name", "Unknown")
                location = item.get("location", {}).get("display_name", "India")
                description = (item.get("description") or "").strip()
                url = (item.get("redirect_url") or "").strip()
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary = None
                if salary_min or salary_max:
                    parts = []
                    if salary_min:
                        parts.append(f"₹{salary_min:,.0f}")
                    if salary_max:
                        parts.append(f"₹{salary_max:,.0f}")
                    salary = " - ".join(parts)

                if not title or not url:
                    continue

                jobs.append(JobPost(
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    source="adzuna",
                    description=description,
                    salary=salary,
                ))
        except Exception as e:
            errors.append(f"adzuna: {e}")

        return ScrapeResult(source="adzuna", jobs=jobs, errors=errors)
