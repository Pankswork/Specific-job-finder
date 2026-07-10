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

    if "checkpoint" in page.url.lower() or ("login" in page.url.lower() and "feed" not in page.url):
        print("\nLinkedIn login requires manual setup once. Run: python scripts/setup_linkedin.py")
        print("This will open a browser for you to sign in and save cookies.\n")
        return False

    if "feed" in page.url or "login" not in page.url.lower():
        save_cookies(context)
        return True

    print("\nLinkedIn login failed. Run: python scripts/setup_linkedin.py")
    return False



