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


def login(page, context) -> bool:
    email, password = load_credentials()
    if not email or not password:
        return False

    if load_cookies(context):
        page.goto("https://www.linkedin.com/feed/", timeout=15000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        if "feed" in page.url and "login" not in page.url.lower():
            return True

    page.goto("https://www.linkedin.com/login", timeout=15000, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    try:
        page.fill("#username", email, timeout=5000)
        page.fill("#password", password, timeout=5000)
        page.click("button[type=submit]", timeout=5000)
        page.wait_for_timeout(5000)
    except Exception:
        return False

    if "checkpoint" in page.url.lower():
        print("LinkedIn: security checkpoint detected — please complete it, then press Enter")
        input()
        page.wait_for_timeout(3000)

    if "feed" in page.url or ("login" not in page.url.lower() and "checkpoint" not in page.url.lower()):
        save_cookies(context)
        return True

    return False
