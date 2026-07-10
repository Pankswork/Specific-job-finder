import re
import time

import requests
from bs4 import BeautifulSoup

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper


class LinkedInPostsScraper(BaseScraper):
    site_name = "linkedin_posts"

    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []

        queries = [
            "site:linkedin.com/posts devops fresher hiring 2026",
            "site:linkedin.com/posts devops intern hiring 2026",
        ]

        seen: set[str] = set()

        for q in queries:
            try:
                resp = requests.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": q},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                    },
                    timeout=15,
                )
                soup = BeautifulSoup(resp.text, "html.parser")
                for item in soup.select(".result__body"):
                    link = item.select_one(".result__title a")
                    snippet = item.select_one(".result__snippet")
                    url = link.get("href", "") if link else ""
                    if not url or "linkedin.com/posts/" not in url:
                        continue
                    if url in seen:
                        continue
                    seen.add(url)
                    text = snippet.get_text(strip=True) if snippet else ""
                    jobs.append(JobPost(
                        title="",
                        company="",
                        location="India",
                        url=url,
                        source="linkedin_posts",
                        description=text[:2000],
                    ))
            except Exception as e:
                errors.append(f"linkedin_posts search: {e}")

        return ScrapeResult(source=self.site_name, jobs=jobs, errors=errors)
