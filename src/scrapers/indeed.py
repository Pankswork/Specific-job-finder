import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlencode

import requests

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

INDEED_BASE = "https://www.indeed.com/rss"


class IndeedScraper(BaseScraper):
    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        queries = self.config.get("queries", [])
        max_pages = self.config.get("max_pages", 1)

        for query in queries:
            for page in range(max_pages):
                params = {"q": query["q"], "l": query.get("l", ""), "start": page * 10}
                url = f"{INDEED_BASE}?{urlencode(params)}"
                try:
                    resp = requests.get(url, timeout=20)
                    resp.raise_for_status()
                    parsed = self._parse_rss(resp.text, query)
                    jobs.extend(parsed)
                except Exception as e:
                    errors.append(f"Indeed RSS failed for {query['q']}: {e}")

        return ScrapeResult(source="indeed", jobs=jobs, errors=errors)

    def _parse_rss(self, xml: str, query: dict) -> list[JobPost]:
        jobs: list[JobPost] = []
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return jobs

        ns = {"": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//item", ns) or root.findall(".//entry", ns):
            title = _get_text(entry, "title")
            link = _get_text(entry, "link")
            description = _get_text(entry, "description")
            pub_date = _get_text(entry, "pubDate") or _get_text(entry, "published")

            if not title or not link:
                continue

            company = self._extract_company(title, description)
            location = query.get("l", "Unknown")

            jobs.append(JobPost(
                title=title.strip(),
                company=company,
                location=location,
                url=link.strip(),
                source="indeed",
                description=(description or "").strip(),
                posted_date=pub_date,
            ))
        return jobs

    def _extract_company(self, title: str, description: str) -> str:
        if " - " in title:
            return title.split(" - ", 1)[1].split(" - ")[0].strip()
        if description:
            for line in description.split("\n"):
                line = line.strip()
                if line.startswith("- ") and "Company:" in line:
                    return line.split("Company:")[1].strip()
        return "Unknown"


def _get_text(parent: ET.Element, tag: str) -> str | None:
    elem = parent.find(tag)
    if elem is not None and elem.text:
        return elem.text
    elem = parent.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
    if elem is not None and elem.text:
        return elem.text
    return None
