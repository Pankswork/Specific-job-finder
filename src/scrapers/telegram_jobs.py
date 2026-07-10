import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper

TELEGRAM_CHANNELS = [
    "devopsbuddys",
    "devopsjobsinbangalore",
    "getjobss",
    "fresheroffcampus",
]

TITLE_KEYWORDS = [
    "devops", "sre", "site reliability", "platform engineer",
    "cloud engineer", "cloud intern", "devsecops",
    "infrastructure engineer", "aws engineer", "kubernetes",
    "k8s", "terraform", "release engineer", "ci/cd",
]

EXCLUDE_KEYWORDS = [
    "teacher", "professor", "social media", "marketing",
    "hr ", "human resource", "data entry", "administrative",
    "customer support", "customer service", "sales", "recruiter",
    "designer", "writer", "editor", "accountant", "finance",
    "content", "creative", "driver", "delivery",
]


def _is_relevant(text: str) -> bool:
    text_lower = text.lower()
    if any(excl in text_lower for excl in EXCLUDE_KEYWORDS):
        return False
    return any(kw in text_lower for kw in TITLE_KEYWORDS)


def _extract_title(text: str) -> str:
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if any(kw in line.lower() for kw in ["position", "hiring", "opening", "role", "job title"]):
            parts = re.split(r":|–|-", line, maxsplit=1)
            if len(parts) > 1:
                return parts[1].strip()
            return line
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) < 80 and not line.startswith("#") and not line.startswith("http"):
            return line
    return ""


def _extract_company(text: str) -> str:
    patterns = [
        r"(?:company|organization|firm)\s*(?::|is|-)?\s*(.+?)(?:\n|\.)",
        r"@\s*(\w+(?:\s+\w+){0,3})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown"


def _extract_location(text: str) -> str:
    for pat in [
        r"(?:location|place|city|work from)\s*(?::|is|-)?\s*(.+?)(?:\n|\.)",
        r"📍\s*(.+?)(?:\n|\.)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            loc = m.group(1).strip()
            if len(loc) < 50:
                return loc
    return "India"


def _extract_apply_url(text: str) -> str:
    urls = re.findall(r"https?://[^\s\n\)]+", text)
    for u in urls:
        if "t.me/" not in u and "whatsapp.com" not in u:
            return u
    return urls[0] if urls else ""


class TelegramJobsScraper(BaseScraper):
    site_name = "telegram_jobs"

    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []
        channels = self.config.get("channels", TELEGRAM_CHANNELS)
        max_per_channel = self.config.get("max_per_channel", 20)

        for channel in channels:
            try:
                resp = requests.get(
                    f"https://t.me/s/{channel}",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                for msg in soup.select(".tgme_widget_message_wrap")[:max_per_channel]:
                    text_el = msg.select_one(".tgme_widget_message_text")
                    if not text_el:
                        continue
                    text = text_el.get_text(strip=True)
                    if not text or len(text) < 80:
                        continue

                    title = _extract_title(text)
                    if not title:
                        continue
                    if not _is_relevant(f"{title} {text[:500]}"):
                        continue

                    date_el = msg.select_one("time")
                    posted_date = date_el.get("datetime") if date_el else None

                    if posted_date:
                        try:
                            d = datetime.fromisoformat(posted_date.replace("Z", "+00:00"))
                            if (datetime.now(timezone.utc) - d).days > 0:
                                continue
                        except ValueError:
                            pass

                    link_el = msg.select_one("a.tgme_widget_message_date")
                    url = link_el.get("href") if link_el else f"https://t.me/s/{channel}"

                    apply_url = _extract_apply_url(text)

                    jobs.append(JobPost(
                        title=title,
                        company=_extract_company(text),
                        location=_extract_location(text),
                        url=apply_url or url,
                        source=f"telegram_{channel}",
                        description=text[:2000],
                        posted_date=posted_date,
                    ))
            except Exception as e:
                errors.append(f"telegram_{channel}: {e}")

        return ScrapeResult(source=self.site_name, jobs=jobs, errors=errors)
