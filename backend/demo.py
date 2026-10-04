"""Terminal demo of the core logic, without the web server. Uses straight-line distances only
(no Google requests). Run from the repo root:   python backend/demo.py

Change the settings below to try other buildings, users and locations.
"""
from datetime import date, time, timedelta

from parking.data import BUILDINGS, LOTS, lot_label, zone_letter
from parking.geo import make_point
from parking.prices import dollars
from parking.ranking import PRIORITIES, WALK_LIMIT_MIN, WALK_METRES_PER_MIN, nearest_lots, pick
from parking.reminders import plan_reminder
from parking.search import find, search_buildings, suggest

BUILDING_NAME = "Olson Hall"
AFFILIATION = "student"          # "student", "staff" or "visitor"
CLASS_HOUR = 10                  # 24-hour clock, so 18 = 6pm
SEARCH = "well"                  # what someone types in the building box
MY_LAT, MY_LNG = 38.5423, -121.7496   # standing at the Memorial Union

SAMPLE_SETTINGS = {"affiliation": AFFILIATION, "lead_minutes": 30, "walk_limit_min": WALK_LIMIT_MIN, "priority": "best"}
SAMPLE_SCHEDULE = [   # building may be None: the reminder still goes out
    {"course": "ECS 36A",     "days": [1, 3, 5], "start": time(10, 0),  "building": find(BUILDINGS, "Olson Hall")},
    {"course": "MAT 21C",     "days": [2, 4],    "start": time(12, 10), "building": None},
    {"course": "ECS 36A LAB", "days": [3],       "start": time(8, 0),   "building": find(BUILDINGS, "Kemper Hall")},
    {"course": "PHY 9A",      "days": [1, 3],    "start": time(14, 10), "building": find(BUILDINGS, "Giedt Hall")},
    {"course": "STA 13",      "days": [5],       "start": time(9, 0),   "building": None},
]


def describe(item):
    metres, price, lot = item
    return f"{lot_label(lot)} ({zone_letter(lot)}, {dollars(price)}), {metres:.0f} m, ~{metres / WALK_METRES_PER_MIN:.0f} min walk"


def show_picks(ranked):
    for priority in PRIORITIES:
        print(f"  {priority.capitalize():<9} {describe(pick(ranked, priority, WALK_LIMIT_MIN))}")


if __name__ == "__main__":
    print(f'Search "{SEARCH}":')
    for building in search_buildings(BUILDINGS, SEARCH):
        print(f"  {building['properties']['loc_name']:<34} {building['properties']['type1_name']}")

    building = find(BUILDINGS, BUILDING_NAME)
    if building is None:
        print(f'No building called "{BUILDING_NAME}". Did you mean: {suggest(BUILDINGS, BUILDING_NAME)}?')
    else:
        print(f"\nFrom {building['properties']['loc_name']}, {AFFILIATION} at {CLASS_HOUR}:00 (walk limit {WALK_LIMIT_MIN} min):")
        show_picks(nearest_lots(building, LOTS, AFFILIATION, CLASS_HOUR))

    print(f"\nFrom your location ({MY_LAT}, {MY_LNG}), {AFFILIATION} at {CLASS_HOUR}:00:")
    show_picks(nearest_lots(make_point(MY_LAT, MY_LNG), LOTS, AFFILIATION, CLASS_HOUR))

    print("\nReminders, Nov 2-15:")
    day = date(2026, 11, 2)
    while day <= date(2026, 11, 15):
        reminder, reason = plan_reminder(day, SAMPLE_SCHEDULE, SAMPLE_SETTINGS, LOTS)
        if reminder:
            print(f"  {day:%a %b %d}  remind {reminder['remind_at']:%H:%M}  {reminder['message']}")
        else:
            print(f"  {day:%a %b %d}  no reminder ({reason})")
        day += timedelta(days=1)
