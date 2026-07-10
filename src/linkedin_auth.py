import json
import os
from pathlib import Path

_COOKIE_FILE = Path("data/linkedin_cookies.json")


def load_credentials() -> tuple[str, str]:
    from dotenv import load_dotenv
    load_dotenv()
    email = os.environ.get("LINKEDIN_EMAIL", "")
    password = os.environ.get("LINKEDIN_PASSWORD", "")
    return email, password


def save_cookies(context):
    _COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cookies = context.cookies()
    _COOKIE_FILE.write_text(json.dumps(cookies))
    return cookies


def load_cookies(context) -> bool:
    if _COOKIE_FILE.exists():
        try:
            cookies = json.loads(_COOKIE_FILE.read_text())
            context.add_cookies(cookies)
            return True
        except Exception:
            pass
    return False


def clear_cookies():
    if _COOKIE_FILE.exists():
        _COOKIE_FILE.unlink()


def _make_inputs_visible(page):
    page.evaluate("""() => {
        document.querySelectorAll('input').forEach(inp => {
            inp.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important;position:static!important';
        });
        document.querySelectorAll('div').forEach(div => {
            if (div.querySelector('input')) {
                div.style.cssText = 'display:block!important;visibility:visible!important;opacity:1!important';
            }
        });
    }""")


def login(page, context) -> bool:
    email, password = load_credentials()
    if not email or not password:
        return False

    if load_cookies(context):
        page.goto("https://www.linkedin.com/feed/", timeout=15000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        if "feed" in page.url and "login" not in page.url.lower():
            return True

    from playwright_stealth import Stealth
    Stealth().apply_stealth_sync(page)

    page.goto("https://www.linkedin.com/login", timeout=15000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    try:
        _make_inputs_visible(page)
        page.wait_for_timeout(500)

        email_inp = page.locator("input[type='email']").first
        if email_inp.is_visible():
            email_inp.fill(email)
            page.wait_for_timeout(1000)

        pw_inp = page.locator("input[type='password']").first
        if pw_inp.is_visible():
            pw_inp.fill(password)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
        else:
            page.evaluate("""(pw) => {
                const inp = Array.from(document.querySelectorAll('input')).find(i => i.type === 'password');
                if (!inp) return;
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(inp, pw);
                inp.dispatchEvent(new Event('input', {bubbles: true}));
            }""", password)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")

        page.wait_for_timeout(5000)
    except Exception:
        pass

    if "checkpoint" in page.url.lower():
        print("\nLinkedIn security challenge: open a headed browser to complete it once.")
        print("Cookies will be saved for future runs.")
        return _headed_login(email, password)

    if "feed" in page.url or "login" not in page.url.lower():
        save_cookies(context)
        return True

    print("\nLinkedIn login failed — open a headed browser for manual login.")
    return _headed_login(email, password)


def _headed_login(email: str, password: str) -> bool:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto("https://www.linkedin.com/login", timeout=30000)
        page.wait_for_timeout(2000)

        print("\nA browser window has opened. Please log in to LinkedIn manually.")
        print("After signing in, press Enter here to save cookies and continue...")
        input()

        page.wait_for_timeout(3000)
        if "feed" in page.url or "login" not in page.url.lower():
            save_cookies(context)
            browser.close()
            return True

        browser.close()
    return False
