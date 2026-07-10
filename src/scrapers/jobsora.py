import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

TITLE_KEYWORDS = [
    "devops", "sre", "site reliability", "platform engineer",
    "cloud engineer", "cloud intern", "devsecops",
    "infrastructure engineer", "aws engineer", "kubernetes",
    "k8s", "terraform", "release engineer", "ci/cd",
    "system administrator", "linux administrator",
]

EXCLUDE_TITLES = [
    "teacher", "professor", "docente", "social media", "marketing",
    "hr ", "human resource", "data entry", "administrative",
    "customer support", "customer service", "sales", "recruiter",
    "designer", "writer", "editor", "accountant", "finance",
    "content", "creative",
]


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    if any(excl in title_lower for excl in EXCLUDE_TITLES):
        return False
    return any(kw in title_lower for kw in TITLE_KEYWORDS)


class JobsoraScraper(BaseScraper):
    def scrape(self) -> ScrapeResult:
        from bs4 import BeautifulSoup

        jobs: list[JobPost] = []
        errors: list[str] = []
        query = self.config.get("query", "devops")
        location = self.config.get("location", "Bangalore")
        max_jobs = self.config.get("max_jobs", 30)

        for page in range(2):
            if len(jobs) >= max_jobs:
                break

            url = f"https://in.jobsora.com/jobs?q={query}&l={location}&page={page}"
            try:
                resp = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=20,
                )
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")
                for card in soup.select(".js-listing-item"):
                    title_el = card.select_one('[class*="title"], h2, h3, .c-job-item__title')
                    company_el = card.select_one('[class*="company"], .c-job-item__company')
                    location_el = card.select_one('[class*="location"], .c-job-item__location')
                    salary_el = card.select_one('[class*="salary"]')
                    link_el = card.select_one("a[href*='/job-']")

                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title or not _is_relevant(title):
                        continue

                    jobs.append(JobPost(
                        title=title,
                        company=company_el.get_text(strip=True) if company_el else "Unknown",
                        location=location_el.get_text(strip=True) if location_el else location,
                        url=link_el.get("href") if link_el else "",
                        source="jobsora",
                        description="",
                        salary=salary_el.get_text(strip=True) if salary_el else None,
                    ))

                    if len(jobs) >= max_jobs:
                        break
            except Exception as e:
                errors.append(f"Jobsora: {e}")

        return ScrapeResult(source="jobsora", jobs=jobs, errors=errors)
