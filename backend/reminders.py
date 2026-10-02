from datetime import date, datetime, time, timedelta

from howfar import (WALK_LIMIT_MIN, WALK_METRES_PER_MIN, distance, dollars, find, load, lot_label,
                    price_for, zone_letter)

# --- Settings for one user (later: the users and reminder_settings tables) ---
AFFILIATION = "student"
LEAD_MINUTES = 30          # remind this long before the first class

# --- Sample schedule (later: manual entry or the parser fills the schedule_entries table) ---
# days use ISO numbers: 1 = Monday ... 7 = Sunday
# building is optional: None means the user skipped it or the parser couldn't match it
SCHEDULE = [
    {"course": "ECS 36A",     "days": [1, 3, 5], "start": time(10, 0),  "building": "Olson Hall"},
    {"course": "MAT 21C",     "days": [2, 4],    "start": time(12, 10), "building": None},
    {"course": "ECS 36A LAB", "days": [3],       "start": time(8, 0),   "building": "Kemper Hall"},
    {"course": "PHY 9A",      "days": [1, 3],    "start": time(14, 10), "building": "Giedt Hall"},
    {"course": "STA 13",      "days": [5],       "start": time(9, 0),   "building": None},
]

# --- Academic calendar (later: the terms and closures tables) ---
# PLACEHOLDER dates: check them against the UC Davis academic calendar
TERM_START = date(2026, 9, 23)
TERM_END = date(2026, 12, 11)
CLOSURES = {
    date(2026, 11, 11): "Veterans Day",
    date(2026, 11, 26): "Thanksgiving",
    date(2026, 11, 27): "Thanksgiving break",
}


# 1. SKIP: is there any reason not to remind on this date?
def skip_reason(day):
    if not (TERM_START <= day <= TERM_END):
        return "outside the quarter"
    if day.isoweekday() >= 6:              # 6 = Saturday, 7 = Sunday
        return "weekend"
    if day in CLOSURES:
        return CLOSURES[day]
    return None


# 2. TODAY'S CLASSES: entries whose days include this date's weekday, earliest first
def classes_on(day):
    todays = [entry for entry in SCHEDULE if day.isoweekday() in entry["days"]]
    todays.sort(key=lambda entry: entry["start"])
    return todays


# 3. LOT: the cheapest allowed lot where the day's LONGEST walk stays within the limit
def best_lot(buildings_today, lots, arrival_hour):
    options = []
    for lot in lots:
        if lot["properties"]["status"] != "Existing":
            continue
        price = price_for(zone_letter(lot), AFFILIATION, arrival_hour)   # you pay when you ARRIVE
        if price is None:
            continue
        longest_walk = max(distance(building, lot) for building in buildings_today)
        options.append((longest_walk, price, lot))

    within_limit = [option for option in options if option[0] / WALK_METRES_PER_MIN <= WALK_LIMIT_MIN]
    if within_limit:
        return min(within_limit, key=lambda option: (option[1], option[0]))   # cheapest, then shortest walk
    return min(options, key=lambda option: option[0])                         # nothing close enough: shortest walk


# 4. PLAN: everything the reminder for one date needs, or the reason there isn't one
def plan_reminder(day, all_buildings, lots):
    reason = skip_reason(day)
    if reason:
        return None, reason

    todays = classes_on(day)
    if not todays:
        return None, "no classes"

    first = todays[0]
    remind_at = datetime.combine(day, first["start"]) - timedelta(minutes=LEAD_MINUTES)

    # The reminder itself only needs the time
    where = f" in {first['building']}" if first["building"] else ""
    message = f"Class at {first['start']:%H:%M}{where}. Don't forget to pay for parking."

    # Bonus: a parking suggestion, but only for the buildings we know.
    # set() removes repeats, so a building with two classes is only counted once
    names = {entry["building"] for entry in todays if entry["building"]}
    buildings_today = [b for b in (find(all_buildings, name) for name in names) if b is not None]
    if buildings_today:
        metres, price, lot = best_lot(buildings_today, lots, first["start"].hour)
        message += (f" Cheapest nearby: {lot_label(lot)} ({zone_letter(lot)} zone, {dollars(price)}), "
                    f"longest walk today {metres / WALK_METRES_PER_MIN:.0f} min.")

    return {"remind_at": remind_at, "message": message}, None


# 5. RUN: print what would be sent each day for a stretch of dates
if __name__ == "__main__":
    all_buildings = load("ucd_buildings.geojson")
    lots = load("ucd_parking_lots.geojson")

    day = date(2026, 11, 2)
    while day <= date(2026, 11, 15):
        reminder, reason = plan_reminder(day, all_buildings, lots)
        if reminder:
            print(f"{day:%a %b %d}  remind {reminder['remind_at']:%H:%M}  {reminder['message']}")
        else:
            print(f"{day:%a %b %d}  no reminder ({reason})")
        day += timedelta(days=1)
