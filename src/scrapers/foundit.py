from src.scrapers.browser import BrowserScraper

TITLE_KEYWORDS = [
    "devops", "sre", "site reliability", "platform engineer",
    "cloud engineer", "cloud intern", "devsecops",
    "infrastructure engineer", "aws engineer", "kubernetes",
    "k8s", "terraform", "release engineer", "ci/cd",
    "system administrator", "linux administrator",
]

EXCLUDE_TITLES = [
    "teacher", "professor", "social media", "marketing",
    "hr ", "human resource", "data entry", "administrative",
    "customer support", "customer service", "sales", "recruiter",
    "designer", "writer", "editor", "accountant", "finance",
    "content", "creative",
]


class FounditScraper(BrowserScraper):
    site_name = "foundit"

    def build_search_url(self) -> str:
        query = self.config.get("query", "devops")
        location = self.config.get("location", "bangalore")
        q = query.replace(" ", "-")
        l = location.replace(" ", "-")
        return f"https://www.foundit.in/search/{q}?location={l}"

    def parse_listings(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select('[class*="card"], [class*="job"], article') or [soup]:
            title_el = card.select_one('[class*="title"], h2, h3, [class*="heading"]')
            company_el = card.select_one('[class*="company"], [class*="org"], [class*="cmp"]')
            location_el = card.select_one('[class*="location"], [class*="loc"]')
            link_el = card.select_one("a[href*='/job/'], a[href*='/jobs/']")

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
