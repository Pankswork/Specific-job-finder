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


class JobslookerScraper(BrowserScraper):
    site_name = "jobslooker"

    def build_search_url(self) -> str:
        query = self.config.get("query", "devops")
        location = self.config.get("location", "bangalore")
        q = query.replace(" ", "+")
        l = location.replace(" ", "+")
        return f"https://in.jobslooker.com/jobs?q={q}&l={l}"

    def parse_listings(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select('[class*="job"], [class*="vacancy"]') or [soup]:
            title_el = card.select_one('[class*="title"], h2, h3, a[class*="title"]')
            company_el = card.select_one('[class*="company"], [class*="org"]')
            location_el = card.select_one('[class*="location"], [class*="loc"]')
            link_el = card.select_one("a[href*='/job/'], a[href*='/vacancy/'], a[href*='-job']")
            salary_el = card.select_one('[class*="salary"], [class*="pay"]')

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
                "salary": salary_el.get_text(strip=True) if salary_el else None,
            })

        return items
