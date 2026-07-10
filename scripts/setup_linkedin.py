"""One-time setup: open a browser, sign into LinkedIn, save cookies for automated runs."""

import sys
sys.path.insert(0, ".")

from playwright.sync_api import sync_playwright
from src.linkedin_auth import save_cookies


def main():
    print("Opening LinkedIn login in a browser...")
    print("Please sign in manually, then press Enter here to save cookies.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.goto("https://www.linkedin.com/login", timeout=30000)
        page.wait_for_timeout(2000)

        input("\nPress Enter after you've signed in on the browser...")
        page.wait_for_timeout(3000)

        if "feed" in page.url or "login" not in page.url.lower():
            save_cookies(context)
            print("Cookies saved to data/linkedin_cookies.json")
            print("LinkedIn scraping will now work in automated runs.")
        else:
            print(f"Still on login page (URL: {page.url[:60]}). Try again.")
            print("Make sure you complete any security challenges.")

        browser.close()


if __name__ == "__main__":
    main()
