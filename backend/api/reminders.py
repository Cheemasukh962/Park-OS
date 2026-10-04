"""GET /api/reminders/preview?from=2026-11-02&to=2026-11-08: what reminder goes out each day, and why not."""
from datetime import date, time, timedelta

from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from api.shapes import suggestion_json
from api.store import read_store
from parking.data import BUILDINGS_BY_ID, LOTS
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


@bp.get("/api/reminders/preview")
def preview():
    start, end = date_range()
    store = read_store()
    settings = store["settings"]

    # Saved classes use building_id and "HH:MM"; the planner wants building features and time objects
    schedule = [{"course": e["course"], "days": e["days"], "start": time.fromisoformat(e["start"]),
                 "building": BUILDINGS_BY_ID.get(e["building_id"])} for e in store["schedule"]]

    # Real walks between every class building and its nearby lots (cached, so usually free)
    class_buildings = list({id(e["building"]): e["building"] for e in schedule if e["building"]}.values())
    walks = WalkTable(class_buildings, LOTS, settings["affiliation"], settings["walk_limit_min"])

    days = []
    day = start
    while day <= end:
        reminder, reason = plan_reminder(day, schedule, settings, LOTS, walks.metres)
        if reminder is None:
            days.append({"date": day.isoformat(), "skipped": reason})
        else:
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
                chosen = suggestion_json(suggestion["chosen"], reminder["buildings"], walks)
                closest = suggestion_json(suggestion["closest"], reminder["buildings"], walks)
                item["suggestion"] = {**chosen, "closest": closest,
                                      "saves_cents": closest["price_cents"] - chosen["price_cents"]}
            days.append(item)
        day += timedelta(days=1)
    return jsonify(days)
