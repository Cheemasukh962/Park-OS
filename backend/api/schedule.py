"""The user's classes: list, add, edit, delete.

GET    /api/schedule        all classes
POST   /api/schedule        add one  → 201 Created
PUT    /api/schedule        replace them all (a list) in one step
POST   /api/schedule/validate   check one without saving it
PUT    /api/schedule/<id>   replace one
DELETE /api/schedule/<id>   remove one → 204 No Content
"""
from flask import Blueprint, jsonify, request

from api.auth import current_user_id
from api.errors import BadRequest
from api.params import parse_hhmm
from api.shapes import entry_json
from db import schedule as db
from parking.data import BUILDINGS_BY_ID

MAX_COURSE = 80        # the database refuses longer names

bp = Blueprint("schedule", __name__)


def validate_entry(body):
    # Check a class sent by the front end, and return the clean version to save
    if not isinstance(body, dict):
        raise BadRequest("send a JSON object")
    course = str(body.get("course", "")).strip()[:MAX_COURSE]
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
    return jsonify([entry_json(e) for e in db.list_entries(current_user_id())])


@bp.post("/api/schedule")
def add_class():
    entry = db.add_entry(current_user_id(), validate_entry(request.get_json(silent=True)))
    return jsonify(entry_json(entry)), 201


@bp.put("/api/schedule")
def replace_classes():
    # Replace the whole schedule in ONE request (used when finishing onboarding), so saving
    # can't half-succeed the way 11 separate deletes + 11 adds could
    body = request.get_json(silent=True)
    if not isinstance(body, list):
        raise BadRequest("send a JSON list of classes")
    entries = [validate_entry(item) for item in body]              # all valid, or nothing is saved
    saved = db.replace_entries(current_user_id(), entries)
    return jsonify([entry_json(e) for e in saved])


@bp.put("/api/schedule/<int:entry_id>")
def update_class(entry_id):
    entry = db.update_entry(current_user_id(), entry_id, validate_entry(request.get_json(silent=True)))
    if entry is None:
        return jsonify({"error": f"no class with id {entry_id}"}), 404
    return jsonify(entry_json(entry))


@bp.delete("/api/schedule/<int:entry_id>")
def delete_class(entry_id):
    if not db.delete_entry(current_user_id(), entry_id):
        return jsonify({"error": f"no class with id {entry_id}"}), 404
    return "", 204
