"""Turning saved data into what the parking/ functions take, shared by the routes that plan things."""
from datetime import time

from parking.data import BUILDINGS_BY_ID


def saved_schedule(store):
    # Saved classes ("HH:MM", building_id) → planner classes (time objects, building features)
    return [{"course": e["course"], "days": e["days"], "start": time.fromisoformat(e["start"]),
             "building_id": e["building_id"], "building": BUILDINGS_BY_ID.get(e["building_id"])}
            for e in store["schedule"]]
