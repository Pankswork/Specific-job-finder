import json
import os
from pathlib import Path

_COOKIE_FILE = Path("data/linkedin_cookies.json")
_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});
"""


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


def login(page, context) -> bool:
    email, password = load_credentials()
    if not email or not password:
        return False

    if load_cookies(context):
        page.goto("https://www.linkedin.com/feed/", timeout=15000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        if "feed" in page.url and "login" not in page.url.lower():
            return True

    page.add_init_script("""Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};""")

    page.goto("https://www.linkedin.com/login", timeout=15000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    try:
        page.evaluate("""(args) => {
            const inputs = document.querySelectorAll('input');
            const emailInp = Array.from(inputs).find(i => i.type === 'email');
            if (!emailInp) return;
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(emailInp, args.email);
            emailInp.dispatchEvent(new Event('input', {bubbles: true}));
            emailInp.dispatchEvent(new Event('change', {bubbles: true}));
            emailInp.dispatchEvent(new Event('blur'));
        }""", {"email": email})
        page.wait_for_timeout(1500)

        submit = page.query_selector("button[type=submit]")
        if submit:
            submit.click()
        page.wait_for_timeout(1500)

        pw_field = page.locator("input[type='password']").first
        pw_visible = pw_field.is_visible()
        if pw_visible:
            pw_field.fill(password)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
        else:
            page.evaluate("""(args) => {
                const pw = Array.from(document.querySelectorAll('input')).find(i => i.type === 'password');
                if (!pw) return;
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(pw, args.pw);
                pw.dispatchEvent(new Event('input', {bubbles: true}));
                pw.dispatchEvent(new Event('change', {bubbles: true}));
            }""", {"pw": password})
            page.wait_for_timeout(500)
            page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Sign in'));
                if (btn) btn.click();
            }""")

        page.wait_for_timeout(5000)
    except Exception:
        pass

    if "checkpoint" in page.url.lower():
        print("LinkedIn: security checkpoint — open a headed browser session.")
        return _headed_login(email, password)

    if "feed" in page.url or "login" not in page.url.lower():
        save_cookies(context)
        return True

    print("LinkedIn: automated login failed — trying manual login.")
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
