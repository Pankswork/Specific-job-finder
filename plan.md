# Plan

## Objective
Scrape DevOps fresher/intern/entry-level jobs from multiple sources, score them by skill-match (no LLM), notify via Telegram.

## Current State (July 10, 2026)

### Working Scrapers
- **LinkedIn Jobs** (`linkedin.py`) — 30 jobs, last 24h, intern/entry/associate, sorted by recent. Fetches descriptions for top 20 by navigating to each job URL.
- **LinkedIn Posts** (`linkedin_posts.py`) — searches content posts for fresher DevOps roles. **Requires login cookies** (run `scripts/setup_linkedin.py` once).
- **WeWorkRemotely** (`rss.py`) — 15 jobs, RSS feeds.
- **Hirist** (`indian_jobs.py`) — 20 jobs, HTTP API (gladiator.hirist.tech).
- **Adzuna** (`adzuna.py`) — 20 jobs, official API (needs `ADZUNA_APP_ID` + `ADZUNA_API_KEY` env vars).

### Returning 0 (Not Blocked)
- **RemoteOK** — API works, just no DevOps listings currently.
- **Jobsora** — HTML scraper fixed, just no DevOps listings currently.

### Blocked / Disabled
- **Foundit** — Akamai CDN blocks all requests.
- **Jooble** — Cloudflare challenge.
- **Telegram Jobs** — web preview is cached (hours/days stale), needs bot API for real-time.

### Filters
- All scrapers: **last 24 hours** (`max_job_age_days: 1` in settings.yaml).
- LinkedIn: `f_TPR=r86400`, `f_E=1,2,3`, `sortBy=DD`.
- Scorer: rule-based (50 base + 8/skill + 10 Bangalore + 5 remote + 10 AI). Senior title / 3+yr exp / unpaid → 0.
- Threshold: 60 notify, 85 strong.

### Scoring (no API calls)
- Rule-based in `src/scorer.py`.
- Matches skills from `config/profile.json` against `title + description`.
- Filters senior keywords (senior/lead/staff/sr./sme/expert) and experience >= 3yr.

### LinkedIn Auth
- `.env` file has `LINKEDIN_EMAIL` + `LINKEDIN_PASSWORD`.
- First-time setup: `python scripts/setup_linkedin.py` (headed browser, manual login).
- Cookies saved to `data/linkedin_cookies.json` (gitignored).
- Subsequent runs: loads cookies, skips login.

### Telegram
- Bot: @Panksjobbot (token in env var `TELEGRAM_BOT_TOKEN`).
- Chat ID: `480883256`.

### CI
- GitHub Actions runs without LinkedIn (Playwright not available).
- Local runs with Playwright get all 4 sources (~85-115 jobs).

## Remaining / Todo
1. Run `scripts/setup_linkedin.py` to get fresh cookies for LinkedIn posts.
2. Test full pipeline with LinkedIn login working (jobs + posts).
3. Consider adding more Adzuna queries (sre, cloud engineer) to increase volume.
4. Set up local cron for automated runs on this machine.
5. Maybe revive Telegram scraper with bot API if channels are active.
