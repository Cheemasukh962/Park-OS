"""Loading one user's saved data (from the database, see db/) in the shape the planning code reads:

    {"settings": {...}, "schedule": [classes], "custom_reminders": {"2026-10-03": {"remind_at": "20:55"}}}

Routes that change data call the db/ functions directly (db.schedule.add_entry, ...).
"""
from db.reminders import custom_reminders
from db.schedule import list_entries
from db.settings import get_settings


def read_store(user_id):
    return {"settings": get_settings(user_id), "schedule": list_entries(user_id),
            "custom_reminders": custom_reminders(user_id)}
