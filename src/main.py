import sys
from datetime import datetime, timezone

from src.config import load_profile, load_settings
from src.models import RunSummary
from src.notifier import send_notification
from src.scorer import score_jobs
from src.scrapers import get_enabled_scrapers
from src.tracker import filter_new_jobs, record_scored


def main():
    settings = load_settings()
    profile = load_profile()
    app_settings = settings.get("app", {})
    scoring_settings = settings.get("scoring", {})
    threshold_notify = scoring_settings.get("threshold_notify", 75)

    print(f"[{datetime.now(timezone.utc).isoformat()}] {app_settings.get('name', 'Job Agent')} v{app_settings.get('version', '0')}")
    print(f"Profile: {profile['name']} | Target: {', '.join(profile['target_roles'])}")
    print()

    scrapers = get_enabled_scrapers(settings)
    if not scrapers:
        print("No scrapers enabled. Check config/settings.yaml")
        sys.exit(0)

    all_jobs = []
    errors = []
    for scraper in scrapers:
        print(f"Scraping {scraper.__class__.__name__}...")
        result = scraper.scrape()
        all_jobs.extend(result.jobs)
        errors.extend(result.errors)
        print(f"  Found {len(result.jobs)} jobs")
        for err in result.errors:
            print(f"  Error: {err}")

    total_found = len(all_jobs)
    print(f"\nTotal jobs found: {total_found}")

    new_jobs = filter_new_jobs(all_jobs)
    print(f"New (unseen) jobs: {len(new_jobs)}")

    if not new_jobs:
        print("No new jobs to score.")
        summary = RunSummary(total_found=total_found, new_jobs=0, scored=0, notified=0, errors=errors)
        send_notification(summary)
        sys.exit(0)

    print(f"\nScoring {len(new_jobs)} jobs with DeepSeek...")
    scored = score_jobs(new_jobs, profile)
    record_scored(scored)

    good_matches = [s for s in scored if s.score >= threshold_notify]
    strong_matches = [s for s in scored if s.score >= scoring_settings.get("threshold_strong", 90)]

    print(f"\nResults:")
    print(f"  Scored:        {len(scored)}")
    print(f"  Notified (≥{threshold_notify}): {len(good_matches)}")
    print(f"  Strong (≥{scoring_settings.get('threshold_strong', 90)}): {len(strong_matches)}")

    for s in sorted(scored, key=lambda x: x.score, reverse=True)[:10]:
        tag = "🟢 STRONG" if s.score >= 90 else "🟡 GOOD" if s.score >= threshold_notify else "⚪"
        print(f"  {tag} [{s.score}/100] {s.job.title} @ {s.job.company}")
        print(f"       {s.job.url}")
        print(f"       {s.reasoning}")

    summary = RunSummary(
        total_found=total_found,
        new_jobs=len(new_jobs),
        scored=len(scored),
        notified=len(good_matches),
        errors=errors,
        scored_jobs=good_matches,
    )
    send_notification(summary)
    print("\nDone.")


if __name__ == "__main__":
    main()
