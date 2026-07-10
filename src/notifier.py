from src.config import get_env
from src.models import RunSummary


def send_notification(summary: RunSummary):
    _send_telegram(summary)


def _send_telegram(summary: RunSummary):
    token = get_env("TELEGRAM_BOT_TOKEN")
    chat_id = get_env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    lines = [
        f"🤖 Job Scan Complete",
        f"Found {summary.total_found} jobs ({summary.new_jobs} new)",
        f"Scored {summary.scored} jobs",
        f"Notified: {summary.notified}",
    ]

    if summary.scored_jobs:
        lines.append("")
        lines.append("Top matches:")
        for sj in summary.scored_jobs[:5]:
            emoji = "🟢" if sj.score >= 85 else "🟡"
            lines.append(f"{emoji} [{sj.score}/100] {sj.job.title} @ {sj.job.company}")
            lines.append(f"   {sj.job.url}")
            if sj.score < 80 and sj.missing_skills:
                lines.append(f"   ⚠️ Missing: {', '.join(sj.missing_skills[:5])}")
            lines.append(f"   {sj.reasoning}")

    if summary.errors:
        lines.append("")
        lines.append(f"⚠️ {len(summary.errors)} error(s)")
        for e in summary.errors[:3]:
            lines.append(f"   • {e}")

    text = "\n".join(lines)

    import requests
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
    except Exception as e:
        print(f"Telegram notify failed: {e}")
