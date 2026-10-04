"""The reminder job: every 30 seconds, send today's reminder email once its time has come.

Rules:
- reminders must be on, and an email address set (Edit reminders)
- only between the reminder time and the first class (no point reminding after class has started)
- at most one email per day: the day is claimed in the sent log BEFORE sending, inside the store's
  lock, so even two copies of the job can't both send it (in Phase 4 the reminders_sent table's
  UNIQUE (user_id, reminder_date) does this)

It runs as a background thread in the Flask server. A production version could use cron or APScheduler.
"""
import threading
import time
from datetime import datetime

from api.reminders import plan_days, send_reminder
from api.store import edit_store, read_store

CHECK_EVERY_SECONDS = 30


def check_once(now=None):
    """Send today's reminder if it's due. Returns what happened, for logging and tests."""
    now = now or datetime.now()
    today = now.date().isoformat()
    store = read_store()
    settings = store["settings"]
    if not settings["reminders_enabled"] or not settings["email"]:
        return "reminders off or no email"
    if today in store["reminders_sent"]:
        return "already handled today"

    day = plan_days(store, now.date(), now.date(), settings)[0]
    if "remind_at" not in day:
        return f"no reminder today ({day['skipped']})"
    remind_at = datetime.fromisoformat(f"{today}T{day['remind_at']}")
    class_starts = datetime.fromisoformat(f"{today}T{day['first_class']['start']}")
    if now < remind_at:
        return f"not yet (due {day['remind_at']})"
    if now >= class_starts:
        return "class already started: too late to remind"

    # Claim the day first, so nothing else sends it; then send; then record how it went
    with edit_store() as saved:
        if today in saved["reminders_sent"]:
            return "already handled today"
        saved["reminders_sent"][today] = {"status": "sending"}
    result = send_reminder(settings["email"], day)
    with edit_store() as saved:
        saved["reminders_sent"][today] = result
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
