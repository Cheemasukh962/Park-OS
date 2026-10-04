"""The user's settings. PUT sends only the keys being changed, e.g. {"lead_minutes": 45}."""
from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from api.store import read_store, write_store
from parking.prices import AFFILIATIONS
from parking.ranking import PRIORITIES

bp = Blueprint("settings", __name__)

# What each setting may be: anything else is rejected with a 400
CHECKS = {
    "affiliation": lambda v: v in AFFILIATIONS,
    "lead_minutes": lambda v: isinstance(v, int) and 0 <= v <= 180,
    "walk_limit_min": lambda v: isinstance(v, int) and 1 <= v <= 30,
    "priority": lambda v: v in PRIORITIES,
    "reminders_enabled": lambda v: isinstance(v, bool),
    "channel": lambda v: v == "email",                  # push comes later
    "email": lambda v: isinstance(v, str),
}


@bp.get("/api/settings")
def get_settings():
    return jsonify(read_store()["settings"])


@bp.put("/api/settings")
def update_settings():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise BadRequest("send a JSON object")
    for key, value in body.items():
        if key not in CHECKS:
            raise BadRequest(f"unknown setting: {key}")
        if not CHECKS[key](value):
            raise BadRequest(f"invalid value for {key}: {value!r}")
    store = read_store()
    store["settings"].update(body)                      # only the keys sent are changed
    write_store(store)
    return jsonify(store["settings"])
