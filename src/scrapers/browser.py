from src.models import JobPost, ScrapeResult
from src.scrapers.base import BaseScraper


class BrowserScraper(BaseScraper):
    site_name: str = "generic"
    login_url: str = ""
    search_url: str = ""

    def build_search_url(self) -> str:
        return ""

    def parse_listings(self, html: str) -> list[dict]:
        return []

    def scrape(self) -> ScrapeResult:
        jobs: list[JobPost] = []
        errors: list[str] = []

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            errors.append(f"{self.site_name}: playwright not installed. Run: pip install playwright && playwright install chromium")
            return ScrapeResult(source=self.site_name, jobs=[], errors=errors)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 900},
                )
                page = context.new_page()
                from playwright_stealth import Stealth
                Stealth().apply_stealth_sync(page)
                page.goto(self.build_search_url(), timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                html = page.content()
                browser.close()

            items = self.parse_listings(html)
            for item in items:
                jobs.append(JobPost(
                    title=item.get("title", ""),
                    company=item.get("company", "Unknown"),
                    location=item.get("location", "India"),
                    url=item.get("url", ""),
                    source=self.site_name,
                    description=item.get("description", ""),
                    salary=item.get("salary"),
                ))
        except Exception as e:
            errors.append(f"{self.site_name}: {e}")

        return ScrapeResult(source=self.site_name, jobs=jobs, errors=errors)
