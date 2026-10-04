"""The reminder job: every 30 seconds, send each user's reminder email for today once its time has come.

Rules (checked separately for every user with reminders on and an email set):
- automatic reminders: only between the reminder time and the first class (no point after class starts)
- custom reminders (a time the user chose): within CUSTOM_GRACE_MIN of that time, so a reminder isn't
  sent hours late if the server was off
- at most one email per user per day: the day is claimed in the reminders_sent table BEFORE sending,
  and that table's primary key (user_id, reminder_date) means only one claim can win, even if two
  copies of the job run at once. Exception: if the user re-times a custom reminder after it was sent,
  it's sent again at the new time (they asked for it; handy for testing and demos)

It runs as a background thread in the Flask server. A production version could use cron or APScheduler.
"""
import threading
import time
from datetime import datetime, timedelta

from api.reminders import plan_days, send_reminder
from api.store import read_store
from db import reminders as db
from db.settings import users_with_reminders

CHECK_EVERY_SECONDS = 30
CUSTOM_GRACE_MIN = 30


def already_sent(sent, day):
    # Sent today already? A custom reminder re-timed since then counts as new
    if sent is None:
        return False
    return not (day.get("custom") and sent.get("remind_at") != day["remind_at"])


def check_user(user_id, now):
    """Send this user's reminder for today if it's due. Returns what happened, for logging and tests."""
    today = now.date()
    store = read_store(user_id)
    sent = db.sent_on(user_id, today)
    if sent is not None and today.isoformat() not in store["custom_reminders"]:
        return "already handled today"                # quick exit: no need to plan the day again

    day = plan_days(store, today, today, store["settings"])[0]
    if "remind_at" not in day:
        return f"no reminder today ({day['skipped']})"
    if already_sent(sent, day):
        return "already handled today"
    remind_at = datetime.combine(today, datetime.strptime(day["remind_at"], "%H:%M").time())
    if now < remind_at:
        return f"not yet (due {day['remind_at']})"
    if day["custom"]:
        if now > remind_at + timedelta(minutes=CUSTOM_GRACE_MIN):
            return "missed: the server wasn't running at that time"
    elif now >= datetime.fromisoformat(f"{today}T{day['first_class']['start']}"):
        return "class already started: too late to remind"

    # Claim the day first, so nothing else sends it; then send; then record how it went
    if not db.claim_day(user_id, today, day["remind_at"], day["custom"]):
        return "already handled today"
    result = send_reminder(store["settings"]["email"], day)
    db.record_sent(user_id, today, result)
    return f"{result['status']}: {result.get('error') or result.get('email_id')}"


def check_once(now=None):
    """Check every user once. Returns {user_id: outcome}."""
    now = now or datetime.now()
    outcomes = {}
    for user_id in users_with_reminders():
        try:
            outcomes[user_id] = check_user(user_id, now)
        except Exception as error:                  # one user's bad data mustn't stop everyone else's reminders
            outcomes[user_id] = f"error: {error}"
    return outcomes


def run_forever():
    while True:
        try:
            for user_id, outcome in check_once().items():
                if outcome.startswith(("sent", "failed", "error")):
                    print(f"[reminder job] {datetime.now():%H:%M:%S} user {user_id}: {outcome}", flush=True)
        except Exception as error:                  # never let one bad check stop the job
            print(f"[reminder job] error: {error}", flush=True)
        time.sleep(CHECK_EVERY_SECONDS)


def start():
    threading.Thread(target=run_forever, name="reminder-job", daemon=True).start()   # daemon: stops with the server
    print("[reminder job] started: checking every 30 s", flush=True)
