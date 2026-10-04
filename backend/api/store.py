"""Saving user data: one user's schedule and settings in backend/store.json (git-ignored).

Temporary: Phase 4 replaces this with the database, and the routes that use it don't change.

Two protections, because Flask handles requests at the same time (one thread each):
- A lock: only one request at a time may read-change-write the file. Without it, two requests
  read the same old data and the second write silently undoes the first (a "lost update").
- Atomic writes: write a temporary file, then swap it in with os.replace(). A reader sees the
  old file or the new one, never a half-written mix (which is what corrupted store.json).
"""
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path

STORE = Path(__file__).resolve().parents[1] / "store.json"     # backend/api/store.py → backend/store.json
_lock = threading.Lock()

DEFAULT_SETTINGS = {
    "affiliation": "student",
    "lead_minutes": 30,
    "walk_limit_min": 10,
    "priority": "best",
    "reminders_enabled": True,
    "channel": "email",
    "email": "",
}


def _read():
    if not STORE.exists():
        return {"settings": dict(DEFAULT_SETTINGS), "schedule": [], "next_id": 1, "reminders_sent": {}}
    store = json.loads(STORE.read_text())
    store.setdefault("reminders_sent", {})       # {"2026-10-05": {...}}: one entry per day, so never twice
    return store


def _write(store):
    temp = STORE.with_name(STORE.name + ".tmp")
    temp.write_text(json.dumps(store, indent=2))
    os.replace(temp, STORE)                      # swaps the whole file in one step


def read_store():
    # For routes that only look at the data
    with _lock:
        return _read()


@contextmanager
def edit_store():
    """For routes that change the data: read, change and save as one locked step.

        with edit_store() as store:
            store["settings"]["lead_minutes"] = 45
    """
    with _lock:
        store = _read()
        yield store
        _write(store)
