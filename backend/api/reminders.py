"""GET /api/reminders/preview?from=2026-11-02&to=2026-11-06: what reminder goes out each day, and why not.

Optional ?lead_minutes=45 previews a different reminder time without saving it (the settings page
uses this, so the "remind at" maths only ever happens here).

Response: {"days": [one entry per date], "summary": {"next_reminder": {...} or null, "saves_cents_total": 550}}
"""
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from api.params import int_param
from api.planning import saved_schedule
from api.shapes import suggestion_json
from api.store import edit_store, read_store
from notify.reminder_email import build_reminder_email
from notify.sender import EmailError, send_email
from parking.data import LOTS
from parking.reminders import plan_reminder
from parking.walks import WalkTable

bp = Blueprint("reminders", __name__)


def date_range():
    try:
        start = date.fromisoformat(request.args.get("from", date.today().isoformat()))
        end = date.fromisoformat(request.args.get("to", (start + timedelta(days=6)).isoformat()))
    except ValueError:
        raise BadRequest('from and to must be dates like "2026-11-02"')
    if not start <= end <= start + timedelta(days=31):
        raise BadRequest("to must be on or after from, and at most 31 days later")
    return start, end


def preview_settings(saved):
    # The saved settings, with an optional "what if" lead time for previewing
    lead = int_param("lead_minutes")
    if lead is None:
        return saved
    if not 0 <= lead <= 180:
        raise BadRequest("lead_minutes must be 0-180")
    return {**saved, "lead_minutes": lead}


@bp.get("/api/reminders/preview")
def preview():
    start, end = date_range()
    store = read_store()
    days = plan_days(store, start, end, preview_settings(store["settings"]))
    return jsonify({"days": days, "summary": summary(days)})


@bp.post("/api/reminders/send-now")
def send_now():
    # TESTING: email the next reminder right away, without waiting for its time.
    # Logged separately, so it doesn't stop that day's real scheduled reminder.
    store = read_store()
    if not store["settings"]["email"]:
        raise BadRequest("add your email under Edit reminders first")
    upcoming = [d for d in plan_days(store, date.today(), date.today() + timedelta(days=7), store["settings"])
                if "remind_at" in d]
    if not upcoming:
        raise BadRequest("no class days in the next week to remind about")
    result = send_reminder(store["settings"]["email"], upcoming[0])
    with edit_store() as saved:
        saved["reminders_sent"].setdefault("tests", []).append({**result, "for_date": upcoming[0]["date"]})
    if result["status"] != "sent":
        raise BadRequest(result["error"])
    return jsonify(result)


@bp.get("/api/reminders/sent")
def sent_log():
    # What the reminder job has sent (or failed to send), by date
    return jsonify(read_store()["reminders_sent"])


def plan_days(store, start, end, settings):
    """The reminder plan for every date from start to end: what the Week page shows,
    what the email says, and what the reminder job sends. One function, so they always agree."""
    schedule = saved_schedule(store)
    # Real walks between every class building and its nearby lots (cached, so usually free)
    class_buildings = list({id(e["building"]): e["building"] for e in schedule if e["building"]}.values())
    walks = WalkTable(class_buildings, LOTS, settings["affiliation"], settings["walk_limit_min"])
    days = []
    day = start
    while day <= end:
        reminder, reason = plan_reminder(day, schedule, settings, LOTS, walks.metres)
        days.append({"date": day.isoformat(), "skipped": reason} if reminder is None
                    else day_json(day, reminder, settings, walks))
        day += timedelta(days=1)
    return days


def send_reminder(to, day):
    # Email one planned day; returns a log entry either way
    subject, html, text = build_reminder_email(day)
    entry = {"to": to, "subject": subject, "sent_at": datetime.now().isoformat(timespec="seconds")}
    try:
        return {**entry, "status": "sent", "email_id": send_email(to, subject, html, text)}
    except EmailError as error:
        return {**entry, "status": "failed", "error": str(error)}


def day_json(day, reminder, settings, walks):
    first, suggestion = reminder["first"], reminder["suggestion"]
    item = {
        "date": day.isoformat(),
        "remind_at": f"{reminder['remind_at']:%H:%M}",
        "first_class": {"course": first["course"], "start": f"{first['start']:%H:%M}",
                        "building_name": reminder["first_building"]},
        "message": reminder["message"],
        "suggestion": None,
    }
    if suggestion:
        buildings = reminder["buildings"]
        context = {"affiliation": settings["affiliation"], "walk_limit_min": settings["walk_limit_min"],
                   "closest_price": suggestion["picks"]["closest"][1]}           # items are (metres, price, lot)
        picks = {priority: suggestion_json(choice, buildings, walks, context)
                 for priority, choice in suggestion["picks"].items()}
        item["suggestion"] = {**suggestion_json(suggestion["chosen"], buildings, walks, context),
                              "closest": picks["closest"], "picks": picks}
    return item


def summary(days):
    # The week at a glance: the next reminder still to come, and the total saved by following the suggestions
    now = datetime.now()
    upcoming = [d for d in days if "remind_at" in d and datetime.fromisoformat(f"{d['date']}T{d['remind_at']}") > now]
    return {
        "next_reminder": {"date": upcoming[0]["date"], "remind_at": upcoming[0]["remind_at"]} if upcoming else None,
        "saves_cents_total": sum(d["suggestion"]["saves_cents"] for d in days if d.get("suggestion")),
    }
