"""Planning one day's reminder: when to send it, what it says, and which lot to suggest.

A schedule is a list of classes like
    {"course": "ECS 36A", "days": [1, 3, 5], "start": time(10, 0), "building": <building feature or None>}
days use ISO numbers (1 = Monday ... 7 = Sunday). building is optional: the reminder always goes
out, and the lot suggestion is only added for the buildings we know.
"""
from datetime import datetime, timedelta

from parking.academic_calendar import skip_reason
from parking.arrival import arrival_time
from parking.data import is_open, lot_label, zone_letter
from parking.geo import distance
from parking.prices import dollars, price_for
from parking.ranking import PRIORITIES, WALK_METRES_PER_MIN, pick



def classes_on(day, schedule):
    # That weekday's classes, earliest first
    todays = [entry for entry in schedule if day.isoweekday() in entry["days"]]
    todays.sort(key=lambda entry: entry["start"])
    return todays


def lot_options(buildings_today, lots, arrival_hour, affiliation, walk=distance):
    # Every allowed lot, ranked by the day's LONGEST walk to any of today's buildings.
    # walk(building, lot) gives metres: the straight line by default, or real Google walks
    options = []
    for lot in lots:
        if not is_open(lot):
            continue
        price = price_for(zone_letter(lot), affiliation, arrival_hour)   # you pay when you ARRIVE
        if price is None:
            continue
        longest_walk = max(walk(building, lot) for building in buildings_today)
        options.append((longest_walk, price, lot))
    options.sort(key=lambda option: option[0])                 # nearest first, as pick() expects
    return options


def plan_reminder(day, schedule, settings, lots, walk=distance, custom_time=None):
    """(reminder, None) for a school day with classes, or (None, reason) otherwise.
    settings needs affiliation, lead_minutes, walk_limit_min and priority.

    custom_time: a time the user chose for this day. It always wins: on a class day it replaces the
    automatic time; on any other day (weekend, holiday, no classes) it creates a reminder."""
    todays = classes_on(day, schedule)
    if custom_time is None:
        reason = skip_reason(day)
        if reason:
            return None, reason
        if not todays:
            return None, "no classes"
    elif not todays:
        # A reminder the user added for a day without classes: just the nudge, no class or lot
        return {"remind_at": datetime.combine(day, custom_time), "custom": True, "first": None,
                "first_building": None, "message": "Your ParkOS reminder: don't forget to pay for parking.",
                "suggestion": None, "buildings": []}, None

    first = todays[0]
    if custom_time is not None:
        remind_at = datetime.combine(day, custom_time)
    else:
        remind_at = datetime.combine(day, first["start"]) - timedelta(minutes=settings["lead_minutes"])

    # The reminder itself only needs the time
    first_building = first["building"]["properties"]["loc_name"] if first["building"] else None
    where = f" in {first_building}" if first_building else ""
    message = f"Class at {first['start']:%H:%M}{where}. Don't forget to pay for parking."

    # Bonus: a lot suggestion for the buildings we know (each building counted once)
    buildings_today = list({id(e["building"]): e["building"] for e in todays if e["building"]}.values())
    suggestion = None
    if buildings_today:
        arrival = arrival_time(day, first["start"])                      # you park before class
        options = lot_options(buildings_today, lots, arrival.hour, settings["affiliation"], walk)
        if options:
            # All three picks, so the Week page's Best / Cheapest / Closest chips can switch;
            # the reminder message uses the user's own priority (same rule as the map)
            picks = {priority: pick(options, priority, settings["walk_limit_min"]) for priority in PRIORITIES}
            suggestion = {"chosen": picks[settings["priority"]], "picks": picks}
            metres, price, lot = suggestion["chosen"]
            message += (f" Suggested lot: {lot_label(lot)} ({zone_letter(lot)} zone, {dollars(price)}), "
                        f"about {metres / WALK_METRES_PER_MIN:.0f} min walk to your furthest class.")

    return {"remind_at": remind_at, "custom": custom_time is not None, "first": first,
            "first_building": first_building, "message": message,
            "suggestion": suggestion, "buildings": buildings_today}, None
