import xml.etree.ElementTree as ET

import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

TITLE_KEYWORDS = [
    "devops", "sre", "site reliability", "platform engineer",
    "cloud engineer", "cloud intern", "devsecops",
    "infrastructure engineer", "aws engineer", "kubernetes",
    "k8s", "terraform", "release engineer", "ci/cd",
]

EXCLUDE_KEYWORDS = [
    "teacher", "professor", "docente", "social media", "marketing",
    "hr ", "human resource", "data entry", "administrative assistant",
    "customer support", "customer service", "sales", "recruiter",
    "designer", "writer", "editor", "accountant", "finance",
]


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    if any(excl in title_lower for excl in EXCLUDE_KEYWORDS):
        return False
    return any(kw in title_lower for kw in TITLE_KEYWORDS)


# We Work Remotely category RSS feeds
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-backend-programming-jobs.rss",
]


class WeWorkRemotelyScraper(BaseScraper):
    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        max_jobs = self.config.get("max_jobs", 15)

        for feed_url in WWR_FEEDS:
            if len(jobs) >= max_jobs:
                break
            try:
                resp = requests.get(feed_url, timeout=20)
                resp.raise_for_status()
                parsed = self._parse_rss(resp.text)
                for j in parsed:
                    if _is_relevant(j.title):
                        jobs.append(j)
                        if len(jobs) >= max_jobs:
                            break
            except Exception as e:
                errors.append(f"WeWorkRemotely ({feed_url}): {e}")

        return ScrapeResult(source="weworkremotely", jobs=jobs, errors=errors)

    def _parse_rss(self, xml: str) -> list[JobPost]:
        jobs: list[JobPost] = []
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return jobs

        for item in root.findall(".//item"):
            title = _get_text(item, "title")
            link = _get_text(item, "link")
            description = _get_text(item, "description")
            pub_date = _get_text(item, "pubDate")

            if not title or not link:
                continue

            jobs.append(JobPost(
                title=title.strip(),
                company=_extract_company(title, description),
                location="Remote",
                url=link.strip(),
                source="weworkremotely",
                description=(description or "").strip(),
                posted_date=pub_date,
            ))
        return jobs


def _get_text(parent: ET.Element, tag: str) -> str | None:
    elem = parent.find(tag)
    if elem is not None and elem.text:
        return elem.text
    return None


def _extract_company(title: str, description: str) -> str:
    if " - " in title:
        return title.split(" - ", 1)[1].split(" - ")[0].strip()
    if description:
        for line in description.split("\n"):
            line = line.strip()
            if "Company:" in line:
                return line.split("Company:")[1].strip()
    return "Unknown"
