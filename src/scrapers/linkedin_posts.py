import re
import time
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from src.linkedin_auth import login
from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

SEARCH_QUERIES = [
    "devops fresher hiring",
    "devops intern hiring",
    "devops engineer fresher",
    "site reliability engineer fresher",
    "cloud engineer fresher",
]


class LinkedInPostsScraper(BaseScraper):
    site_name = "linkedin_posts"
    max_posts = 10

    def _parse_post(self, text: str, url: str, author: str = "") -> JobPost | None:
        if len(text) < 100:
            return None

        if not any(w in text.lower() for w in [
            "fresher", "freshers", "entry.level", "0.1 year", "0.2 year",
            "0 year", "trainee", "intern", "junior", "graduate",
            "2024", "2025", "2026",
        ]):
            return None

        if not any(kw in text.lower() for kw in ["devops", "sre", "cloud", "platform", "site reliability"]):
            return None

        age_hours = None
        for pat in [r"(\d+)\s*(h|hr|hrs|hour|hours)\s*ago", r"(\d+)\s*(d|day|days)\s*ago"]:
            m = re.search(pat, text.lower())
            if m:
                num = int(m.group(1))
                unit = m.group(2)
                age_hours = num if unit.startswith("h") else num * 24
                break
        if age_hours is not None and age_hours > 48:
            return None

        title = ""
        for pat in [
            r"(?:hiring|position|opening|role)\s*(?::|for)?\s*(.+?)(?:\n|\.)",
            r"(?:job\s*(?:title|role|position)\s*(?::|is)?)\s*(.+?)(?:\n|\.)",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                title = m.group(1).strip()
                break

        if not title:
            lines = text.split("\n")
            for line in lines[:5]:
                line = line.strip()
                if any(w in line.lower() for w in ["devops", "sre", "cloud", "platform", "site reliability"]):
                    if len(line) < 80:
                        title = line
                        break

        if not title:
            title = "DevOps Fresher Role"

        location = ""
        for pat in [
            r"(?:location|place|city|work from)\s*(?::|is|-)?\s*(.+?)(?:\n|\.)",
            r"📍\s*(.+?)(?:\n|\.)",
            r"location\s*[:\-–]\s*(\w+(?:\s*\w+){0,4})",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                loc = m.group(1).strip()
                if len(loc) < 50:
                    location = loc
                    break

        company = ""
        if company_el := re.search(r"(?:company|organization|firm|@)\s*(?::|is|-)?\s*(.+?)(?:\n|\.)", text, re.IGNORECASE):
            company = company_el.group(1).strip()

        apply_url = ""
        urls = re.findall(r"https?://[^\s\n\)]+", text)
        for u in urls:
            if "linkedin.com" not in u and "t.me" not in u and "whatsapp.com" not in u:
                apply_url = u
                break

        return JobPost(
            title=title,
            company=company or author or "Unknown",
            location=location or "India",
            url=apply_url or url,
            source="linkedin_posts",
            description=text[:2000],
        )

    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            errors.append("linkedin_posts: playwright not installed")
            return ScrapeResult(source=self.site_name, jobs=[], errors=errors)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 900},
                )
                page = context.new_page()

                if not login(page, context):
                    errors.append("linkedin_posts: login failed")
                    browser.close()
                    return ScrapeResult(source=self.site_name, jobs=[], errors=errors)

                seen: set[str] = set()

                for query in SEARCH_QUERIES:
                    q = query.replace(" ", "%20")
                    url = f"https://www.linkedin.com/search/results/content/?keywords={q}&sortBy=date"
                    try:
                        page.goto(url, timeout=20000, wait_until="domcontentloaded")
                        page.wait_for_timeout(4000)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(2000)

                        soup = BeautifulSoup(page.content(), "html.parser")
                        posts = soup.select(".search-result__occluded-item, .feed-shared-update-v2, .occludable-update, [data-urn]")

                        for post in posts[:self.max_posts]:
                            link = post.select_one("a[href*='/posts/']")
                            post_url = link.get("href") if link else ""

                            text_el = post.select_one(".update-components-text, .feed-shared-text, .break-words")
                            text = text_el.get_text(strip=True) if text_el else ""

                            author_el = post.select_one(".feed-shared-actor__name, .update-components-actor__name")
                            author = author_el.get_text(strip=True) if author_el else ""

                            if not text:
                                continue

                            ident = post_url or text[:100]
                            if ident in seen:
                                continue
                            seen.add(ident)

                            job = self._parse_post(text, post_url or url, author)
                            if job:
                                jobs.append(job)

                    except Exception as e:
                        errors.append(f"linkedin_posts query '{query}': {e}")

                    time.sleep(1)

                browser.close()
        except Exception as e:
            errors.append(f"linkedin_posts: {e}")

        return ScrapeResult(source=self.site_name, jobs=jobs, errors=errors)
