"""The user's classes: list, add, edit, delete.

GET    /api/schedule        all classes
POST   /api/schedule        add one  → 201 Created
PUT    /api/schedule        replace them all (a list) in one step
POST   /api/schedule/validate   check one without saving it
PUT    /api/schedule/<id>   replace one
DELETE /api/schedule/<id>   remove one → 204 No Content
"""
from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from api.params import parse_hhmm
from api.shapes import entry_json
from api.store import edit_store, read_store
from parking.data import BUILDINGS_BY_ID

bp = Blueprint("schedule", __name__)


def validate_entry(body):
    # Check a class sent by the front end, and return the clean version to save
    if not isinstance(body, dict):
        raise BadRequest("send a JSON object")
    course = str(body.get("course", "")).strip()
    days = body.get("days")
    start, end = body.get("start"), body.get("end")
    building_id = body.get("building_id")

    if not course:
        raise BadRequest("course is required")
    if not isinstance(days, list) or not days or not all(isinstance(d, int) and 1 <= d <= 7 for d in days):
        raise BadRequest("days must be a non-empty list of 1-7 (1 = Monday)")
    start_time = parse_hhmm(start)
    end_time = parse_hhmm(end) if end not in (None, "") else None
    if start_time is None:
        raise BadRequest('start must be 24-hour time like "14:10" or "9:00"')
    if end not in (None, "") and end_time is None:
        raise BadRequest('end must be 24-hour time like "15:00", or empty')
    if end_time is not None and end_time <= start_time:
        raise BadRequest("end must be after start")
    if building_id is not None and building_id not in BUILDINGS_BY_ID:
        raise BadRequest("building_id not found (use /api/buildings?q=... to look it up)")

    return {"course": course, "days": sorted(set(days)), "start": f"{start_time:%H:%M}",
            "end": f"{end_time:%H:%M}" if end_time else None, "building_id": building_id}


@bp.post("/api/schedule/validate")
def check_class():
    # Check a class without saving it: returns the cleaned class, or a 400 with what's wrong.
    # The onboarding grid uses this so the rules live only here, in validate_entry()
    return jsonify(validate_entry(request.get_json(silent=True)))


@bp.get("/api/schedule")
def list_classes():
    return jsonify([entry_json(e) for e in read_store()["schedule"]])


@bp.post("/api/schedule")
def add_class():
    entry = validate_entry(request.get_json(silent=True))          # check first, outside the lock
    with edit_store() as store:
        entry = {"id": store["next_id"], **entry}
        store["schedule"].append(entry)
        store["next_id"] += 1
    return jsonify(entry_json(entry)), 201


@bp.put("/api/schedule")
def replace_classes():
    # Replace the whole schedule in ONE request (used when finishing onboarding), so saving
    # can't half-succeed the way 11 separate deletes + 11 adds could
    body = request.get_json(silent=True)
    if not isinstance(body, list):
        raise BadRequest("send a JSON list of classes")
    entries = [validate_entry(item) for item in body]              # all valid, or nothing is saved
    with edit_store() as store:
        store["schedule"] = []
        for entry in entries:
            store["schedule"].append({"id": store["next_id"], **entry})
            store["next_id"] += 1
        saved = list(store["schedule"])
    return jsonify([entry_json(e) for e in saved])


@bp.put("/api/schedule/<int:entry_id>")
def update_class(entry_id):
    entry = validate_entry(request.get_json(silent=True))
    with edit_store() as store:
        for index, current in enumerate(store["schedule"]):
            if current["id"] == entry_id:
                store["schedule"][index] = {"id": entry_id, **entry}
                return jsonify(entry_json(store["schedule"][index]))
    return jsonify({"error": f"no class with id {entry_id}"}), 404


@bp.delete("/api/schedule/<int:entry_id>")
def delete_class(entry_id):
    with edit_store() as store:
        kept = [e for e in store["schedule"] if e["id"] != entry_id]
        found = len(kept) < len(store["schedule"])
        store["schedule"] = kept
    if not found:
        return jsonify({"error": f"no class with id {entry_id}"}), 404
    return "", 204
