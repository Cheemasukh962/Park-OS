"""Shaping results into the JSON the front end expects (docs/PRD.md section 6).

Keeping this in one place means the API's "contract" with the front end is easy to find and change.
"""
from parking.data import BUILDINGS_BY_ID, feature_id, lot_label, zone_letter
from parking.google_routes import directions_url
from parking.prices import access_note
from parking.ranking import WALK_METRES_PER_MIN
from parking.trips import total_s


def minutes(seconds):
    return None if seconds is None else round(seconds / 60)


def building_json(building):
    p = building["properties"]
    return {"id": p["OBJECTID"], "caan": p["pk_CAAN"], "name": p["loc_name"], "category": p["type1_name"]}


def verdicts(price, walk_min, zone, context):
    """What the screens show about a lot, decided here so every screen agrees.
    context: {"affiliation", "walk_limit_min", "closest_price"} for the trip or day."""
    return {
        # Money saved compared with the closest lot (negative = costs more than the closest)
        "saves_cents": context["closest_price"] - price if context.get("closest_price") is not None else 0,
        "over_walk_limit": walk_min is not None and walk_min > context["walk_limit_min"],
        "access_note": access_note(zone, context["affiliation"]),      # e.g. "A: students after 5 pm"
    }


def option_json(option, context):
    # One lot in a trip: price plus each leg we know (null when that leg doesn't apply)
    if option is None:
        return None
    lot = option["lot"]
    walk_min = minutes(option["walk_s"])
    return {
        "lot_id": feature_id(lot),
        "lot_name": lot_label(lot),
        "zone": zone_letter(lot),
        "price_cents": option["price"],
        "walk_min": walk_min,
        "metres": None if option["walk_m"] is None else round(option["walk_m"]),
        "walk_source": option["walk_source"],               # "google", "estimate", or null with no building
        "drive_min": minutes(option["drive_s"]),
        "drive_metres": option["drive_m"],
        "total_min": round(total_s(option) / 60),
        "directions_url": directions_url(lot),             # opens Google Maps driving directions
        **verdicts(option["price"], walk_min, zone_letter(lot), context),
    }


def suggestion_json(item, buildings_today, walk_table, context):
    # A reminder's lot: item is (metres, price, lot) where metres is the day's LONGEST walk
    if item is None:
        return None
    metres, price, lot = item
    furthest = max(buildings_today, key=lambda b: walk_table.metres(b, lot))
    walk_min = round(metres / WALK_METRES_PER_MIN)
    return {
        "lot_id": feature_id(lot),
        "lot_name": lot_label(lot),
        "zone": zone_letter(lot),
        "price_cents": price,
        "walk_min": walk_min,
        "metres": round(walk_table.route_metres(furthest, lot)),
        "walk_source": "google" if all(walk_table.is_real(b, lot) for b in buildings_today) else "estimate",
        "directions_url": directions_url(lot),
        **verdicts(price, walk_min, zone_letter(lot), context),
    }


def entry_json(entry):
    # A saved class, plus its building's name for display
    building = BUILDINGS_BY_ID.get(entry["building_id"])
    return {**entry, "building_name": building["properties"]["loc_name"] if building else None}


def leg_json(route):
    # One leg of a trip for the map, or None
    if route is None:
        return None
    return {"minutes": minutes(route["seconds"]), "metres": route["metres"], "path": route["path"]}
