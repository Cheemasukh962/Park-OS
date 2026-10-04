"""Saving user data: one user's schedule and settings in backend/store.json (git-ignored).

Temporary: Phase 4 replaces read_store()/write_store() with the database, and the routes
that call them don't need to change.
"""
import json
from pathlib import Path

STORE = Path(__file__).resolve().parents[1] / "store.json"     # backend/api/store.py → backend/store.json

DEFAULT_SETTINGS = {
    "affiliation": "student",
    "lead_minutes": 30,
    "walk_limit_min": 10,
    "priority": "best",
    "reminders_enabled": True,
    "channel": "email",
    "email": "",
}


def read_store():
    if not STORE.exists():
        return {"settings": dict(DEFAULT_SETTINGS), "schedule": [], "next_id": 1}
    return json.loads(STORE.read_text())


def write_store(store):
    STORE.write_text(json.dumps(store, indent=2))
