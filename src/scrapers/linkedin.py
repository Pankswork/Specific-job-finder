import time

from src.models import JobPost, ScrapeResult
from src.scrapers.browser import BrowserScraper

LINKEDIN_KEYWORDS = [
    "devops", "cloud engineer", "sre", "site reliability",
    "platform engineer", "devsecops", "kubernetes",
    "infrastructure engineer", "aws",
]


class LinkedInScraper(BrowserScraper):
    site_name = "linkedin"
    keywords = LINKEDIN_KEYWORDS
    max_description_jobs = 20

    def build_search_url(self) -> str:
        query = self.config.get("query", "DevOps")
        location = self.config.get("location", "India")
        q = query.replace(" ", "%20")
        l = location.replace(" ", "%20")
        return f"https://www.linkedin.com/jobs/search/?keywords={q}&location={l}&f_TPR=r86400&f_E=1,2,3&sortBy=DD&position=1&pageNum=0"

    def _extract_description(self, url: str, page) -> str:
        if not url or "/jobs/view" not in url:
            return ""
        try:
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            for sel in [".jobs-description-content__text", ".show-more-less-html__markup",
                        "article.description", ".job-view-layout .description",
                        ".jobs-search__job-details--container"]:
                try:
                    el = page.query_selector(sel)
                    if el:
                        text = el.inner_text().strip()
                        if len(text) > 30:
                            return text
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            errors.append("linkedin: playwright not installed")
            return ScrapeResult(source=self.site_name, jobs=[], errors=errors)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 900},
                )
                page = context.new_page()
                page.goto(self.build_search_url(), timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page.content(), "html.parser")
                raw_cards = soup.select(".job-card-container") or soup.select("[data-job-id]") or soup.select(".base-card")

                for raw in raw_cards[:30]:
                    title_el = raw.select_one(".job-card-list__title, .base-search-card__title, h3")
                    company_el = raw.select_one(".job-card-container__company-name, .base-search-card__subtitle, h4")
                    location_el = raw.select_one(".job-card-container__metadata-wrapper, .base-search-card__metadata, .job-card-container__location")
                    link_el = raw.select_one("a[href*='/jobs/view']")

                    title = title_el.get_text(strip=True) if title_el else ""
                    company = company_el.get_text(strip=True) if company_el else "Unknown"
                    location = location_el.get_text(strip=True) if location_el else "India"
                    url = link_el.get("href") if link_el else ""

                    if not title:
                        continue

                    jobs.append(JobPost(
                        title=title,
                        company=company,
                        location=location,
                        url=url,
                        source="linkedin",
                        description="",
                    ))

                for j in jobs[:self.max_description_jobs]:
                    if j.url:
                        desc = self._extract_description(j.url, page)
                        j.description = desc
                        if desc:
                            time.sleep(1)

                browser.close()
        except Exception as e:
            errors.append(f"linkedin: {e}")

        return ScrapeResult(source=self.site_name, jobs=jobs, errors=errors)
