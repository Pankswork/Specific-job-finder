import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper
from src.scrapers.browser import BrowserScraper

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
    "content", "creative", "housekeeper",
]


class HiristScraper(BaseScraper):
    site_name = "hirist"

    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        query = self.config.get("query", "devops")
        max_jobs = self.config.get("max_jobs", 20)

        try:
            resp = requests.get(
                "https://gladiator.hirist.tech/job/search",
                params={"query": query, "page": 0, "size": max_jobs},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://www.hirist.tech/",
                    "Accept": "application/json",
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("data", []):
                title = (item.get("jobdesignation") or "").strip()
                company = item.get("companyData", {}).get("companyName", "Unknown")
                locs = ", ".join(l["name"] for l in item.get("locations", [])) or "India"
                url = (item.get("jobDetailUrl") or "").strip()
                exp_min = item.get("min")
                exp_max = item.get("max")
                tags = [t["name"] for t in item.get("tags", [])]
                description = f"Experience: {exp_min}-{exp_max} years. Skills: {', '.join(tags)}" if tags else ""
                salary_min = item.get("minSal")
                salary_max = item.get("maxSal")
                salary = None
                if salary_min or salary_max:
                    salary = f"₹{salary_min}L - ₹{salary_max}L"

                posted_date = None
                created_ms = item.get("createdTimeMs")
                if created_ms:
                    from datetime import datetime, timezone
                    posted_date = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc).isoformat()

                title_lower = title.lower()
                if not title or not url:
                    continue
                if any(excl in title_lower for excl in EXCLUDE_TITLES):
                    continue

                jobs.append(JobPost(
                    title=title,
                    company=company,
                    location=locs,
                    url=url,
                    source="hirist",
                    description=description,
                    salary=salary,
                ))
        except Exception as e:
            errors.append(f"hirist: {e}")

        return ScrapeResult(source="hirist", jobs=jobs, errors=errors)


class AmbitionBoxScraper(BrowserScraper):
    site_name = "ambitionbox"

    def build_search_url(self) -> str:
        query = self.config.get("query", "devops")
        location = self.config.get("location", "bangalore")
        return f"https://www.ambitionbox.com/jobs/{query}-jobs-in-{location}"

    def parse_listings(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select('[class*="jobCard"], [class*="-card"]') or [soup]:
            title_el = card.select_one('[class*="title"], h2, h3')
            company_el = card.select_one('[class*="company"], [class*="org"]')
            location_el = card.select_one('[class*="location"], [class*="loc"]')
            link_el = card.select_one("a[href*='/jobs/']")

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            title_lower = title.lower()
            if any(excl in title_lower for excl in EXCLUDE_TITLES):
                continue

            if not any(kw in title_lower for kw in TITLE_KEYWORDS):
                continue

            items.append({
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "Bangalore",
                "url": link_el.get("href") if link_el else "",
                "description": "",
            })

        return items


class BuiltInScraper(BrowserScraper):
    site_name = "builtin"

    def build_search_url(self) -> str:
        query = self.config.get("query", "devops-engineer")
        return f"https://builtin.com/jobs/{query}"

    def parse_listings(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select('[class*="job"], article, [class*="card"]') or [soup]:
            title_el = card.select_one('[class*="title"], h2, h3, a[class*="title"]')
            company_el = card.select_one('[class*="company"], [class*="org"]')
            location_el = card.select_one('[class*="location"], [class*="loc"]')
            link_el = card.select_one("a[href*='/job/']")

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            title_lower = title.lower()
            if any(excl in title_lower for excl in EXCLUDE_TITLES):
                continue

            if not any(kw in title_lower for kw in TITLE_KEYWORDS):
                continue

            items.append({
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "Unknown",
                "location": location_el.get_text(strip=True) if location_el else "Remote",
                "url": link_el.get("href") if link_el else "",
                "description": "",
            })

        return items
