from src.scrapers.browser import BrowserScraper

LINKEDIN_KEYWORDS = [
    "devops", "cloud engineer", "sre", "site reliability",
    "platform engineer", "devsecops", "kubernetes",
    "infrastructure engineer", "aws",
]


class LinkedInScraper(BrowserScraper):
    site_name = "linkedin"
    keywords = LINKEDIN_KEYWORDS

    def build_search_url(self) -> str:
        query = self.config.get("query", "DevOps Engineer")
        location = self.config.get("location", "India")
        q = query.replace(" ", "%20")
        l = location.replace(" ", "%20")
        return f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&f_TPR=r604800&f_E=1,2,3&position=1&pageNum=0"

    def parse_listings(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for card in soup.select(".job-card-container") or soup.select("[data-job-id]") or soup.select(".base-card"):
            title_el = card.select_one(".job-card-list__title, .base-search-card__title, h3")
            company_el = card.select_one(".job-card-container__company-name, .base-search-card__subtitle, h4")
            location_el = card.select_one(".job-card-container__metadata-wrapper, .base-search-card__metadata, .job-card-container__location")
            link_el = card.select_one("a[href*='/jobs/view']")

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            location = location_el.get_text(strip=True) if location_el else "India"
            url = link_el.get("href") if link_el else ""

            if not title:
                continue

            items.append({
                "title": title,
                "company": company or "Unknown",
                "location": location,
                "url": url,
                "description": "",
            })

        return items
