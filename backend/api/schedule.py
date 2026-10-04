"""The user's classes: list, add, edit, delete.

GET    /api/schedule        all classes
POST   /api/schedule        add one  → 201 Created
PUT    /api/schedule/<id>   replace one
DELETE /api/schedule/<id>   remove one → 204 No Content
"""
from datetime import time

from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from api.shapes import entry_json
from api.store import read_store, write_store
from parking.data import BUILDINGS_BY_ID

bp = Blueprint("schedule", __name__)


def parse_hhmm(value):
    # "14:10" → time(14, 10); anything else → None
    try:
        return time.fromisoformat(value) if isinstance(value, str) and len(value) == 5 else None
    except ValueError:
        return None


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
    if parse_hhmm(start) is None:
        raise BadRequest('start must be 24-hour "HH:MM", e.g. "14:10"')
    if end is not None and parse_hhmm(end) is None:
        raise BadRequest('end must be 24-hour "HH:MM" or null')
    if building_id is not None and building_id not in BUILDINGS_BY_ID:
        raise BadRequest("building_id not found (use /api/buildings?q=... to look it up)")

    return {"course": course, "days": sorted(set(days)), "start": start, "end": end, "building_id": building_id}


@bp.get("/api/schedule")
def list_classes():
    return jsonify([entry_json(e) for e in read_store()["schedule"]])


@bp.post("/api/schedule")
def add_class():
    store = read_store()
    entry = {"id": store["next_id"], **validate_entry(request.get_json(silent=True))}
    store["schedule"].append(entry)
    store["next_id"] += 1
    write_store(store)
    return jsonify(entry_json(entry)), 201


@bp.put("/api/schedule/<int:entry_id>")
def update_class(entry_id):
    store = read_store()
    for index, entry in enumerate(store["schedule"]):
        if entry["id"] == entry_id:
            store["schedule"][index] = {"id": entry_id, **validate_entry(request.get_json(silent=True))}
            write_store(store)
            return jsonify(entry_json(store["schedule"][index]))
    return jsonify({"error": f"no class with id {entry_id}"}), 404


@bp.delete("/api/schedule/<int:entry_id>")
def delete_class(entry_id):
    store = read_store()
    kept = [e for e in store["schedule"] if e["id"] != entry_id]
    if len(kept) == len(store["schedule"]):
        return jsonify({"error": f"no class with id {entry_id}"}), 404
    store["schedule"] = kept
    write_store(store)
    return "", 204
