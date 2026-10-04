"""The reminder job: every 30 seconds, send today's reminder email once its time has come.

Rules:
- reminders must be on, and an email address set (Edit reminders)
- automatic reminders: only between the reminder time and the first class (no point after class starts)
- custom reminders (a time the user chose): within CUSTOM_GRACE_MIN of that time, so a reminder isn't
  sent hours late if the server was off
- at most one email per day: the day is claimed in the sent log BEFORE sending, inside the store's
  lock, so even two copies of the job can't both send it (in Phase 4 the reminders_sent table's
  UNIQUE (user_id, reminder_date) does this). Exception: if the user re-times a custom reminder after
  it was sent, it's sent again at the new time (they asked for it; handy for testing and demos)

It runs as a background thread in the Flask server. A production version could use cron or APScheduler.
"""
import threading
import time
from datetime import datetime, timedelta

from api.reminders import plan_days, send_reminder
from api.store import edit_store, read_store

CHECK_EVERY_SECONDS = 30
CUSTOM_GRACE_MIN = 30


def already_sent(sent, day):
    # Sent today already? A custom reminder re-timed since then counts as new
    if sent is None:
        return False
    return not (day.get("custom") and sent.get("remind_at") != day["remind_at"])


def check_once(now=None):
    """Send today's reminder if it's due. Returns what happened, for logging and tests."""
    now = now or datetime.now()
    today = now.date().isoformat()
    store = read_store()
    settings = store["settings"]
    if not settings["reminders_enabled"] or not settings["email"]:
        return "reminders off or no email"
    if today in store["reminders_sent"] and today not in store["custom_reminders"]:
        return "already handled today"                # quick exit: no need to plan the day again

    day = plan_days(store, now.date(), now.date(), settings)[0]
    if "remind_at" not in day:
        return f"no reminder today ({day['skipped']})"
    if already_sent(store["reminders_sent"].get(today), day):
        return "already handled today"
    remind_at = datetime.fromisoformat(f"{today}T{day['remind_at']}")
    if now < remind_at:
        return f"not yet (due {day['remind_at']})"
    if day["custom"]:
        if now > remind_at + timedelta(minutes=CUSTOM_GRACE_MIN):
            return "missed: the server wasn't running at that time"
    elif now >= datetime.fromisoformat(f"{today}T{day['first_class']['start']}"):
        return "class already started: too late to remind"

    # Claim the day first, so nothing else sends it; then send; then record how it went
    with edit_store() as saved:
        if already_sent(saved["reminders_sent"].get(today), day):
            return "already handled today"
        saved["reminders_sent"][today] = {"status": "sending", "remind_at": day["remind_at"]}
    result = send_reminder(settings["email"], day)
    with edit_store() as saved:
        saved["reminders_sent"][today] = {**result, "remind_at": day["remind_at"], "custom": day["custom"]}
    return f"{result['status']}: {result.get('error') or result.get('email_id')}"


def run_forever():
    while True:
        try:
            outcome = check_once()
            if outcome.startswith(("sent", "failed")):
                print(f"[reminder job] {datetime.now():%H:%M:%S} {outcome}", flush=True)
        except Exception as error:                  # never let one bad check stop the job
            print(f"[reminder job] error: {error}", flush=True)
        time.sleep(CHECK_EVERY_SECONDS)


def start():
    threading.Thread(target=run_forever, name="reminder-job", daemon=True).start()   # daemon: stops with the server
    print("[reminder job] started: checking every 30 s", flush=True)
