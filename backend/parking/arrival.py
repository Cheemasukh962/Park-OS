"""When you arrive to park: the one rule the reminders and the map both use.

You park BEFORE class, so parking permission is checked at arrival time, not class time. A 5:10 pm
class means arriving around 4:50 pm, when A lots are still employees-only (students may use A
from 5 pm), so the arrival hour decides which lots are allowed.
"""
from datetime import datetime, timedelta

ARRIVAL_BUFFER_MIN = 20


def arrival_time(day, class_start):
    # date + time(10, 0) → datetime(… 9:40)
    return datetime.combine(day, class_start) - timedelta(minutes=ARRIVAL_BUFFER_MIN)


def next_class_at(schedule, building_id, now=None):
    """The next time a class meets in this building within a week: (date, class) or None.
    schedule entries look like {"course", "days": [1..7], "start": time, "building_id"}."""
    now = now or datetime.now()
    for offset in range(8):
        day = (now + timedelta(days=offset)).date()
        todays = sorted(
            (entry for entry in schedule
             if entry["building_id"] == building_id and day.isoweekday() in entry["days"]
             and (offset > 0 or entry["start"] > now.time())),
            key=lambda entry: entry["start"],
        )
        if todays:
            return day, todays[0]
    return None
