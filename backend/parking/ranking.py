"""Ranking lots by distance, and the Best / Cheapest / Closest picks.

Ranked items are (metres, price_cents, lot). metres is the straight-line distance, or a real
Google walk converted to the same units (google_routes.as_metres), so these rules work for both.
"""
from parking.data import is_open, zone_letter
from parking.geo import distance
from parking.prices import price_for

WALK_METRES_PER_MIN = 80   # straight-line walking estimate. Real walks here were 1.3-2.3x longer
WALK_LIMIT_MIN = 10        # default walk limit (later: users.walk_limit_min)
PRIORITIES = ("best", "cheapest", "closest")


def nearest_lots(origin, lots, affiliation, hour):
    # Every open lot this user may park in at this hour, nearest first.
    # origin is a building or make_point(lat, lng): distance() handles both
    ranked = []
    for lot in lots:
        if not is_open(lot):
            continue
        price = price_for(zone_letter(lot), affiliation, hour)
        if price is None:
            continue
        ranked.append((distance(origin, lot), price, lot))
    ranked.sort(key=lambda item: item[0])                  # sort by the first item: metres
    return ranked


def cheapest_within(ranked, walk_limit_min):
    # Cheapest lot within the walk limit; ties go to the shorter walk
    nearby = [item for item in ranked if item[0] / WALK_METRES_PER_MIN <= walk_limit_min]
    if not nearby:
        return None
    return min(nearby, key=lambda item: (item[1], item[0]))   # compare price first, then metres


def pick(ranked, priority, walk_limit_min):
    # One lot from a nearest-first list, matching the front end's Best / Cheapest / Closest chips
    if not ranked:
        return None
    if priority == "closest":
        return ranked[0]                                       # already sorted nearest first
    if priority == "cheapest":
        return min(ranked, key=lambda item: (item[1], item[0]))   # ignore the walk limit
    if priority == "best":
        return cheapest_within(ranked, walk_limit_min) or ranked[0]   # nothing close enough: closest
    raise ValueError(f"priority must be one of {PRIORITIES}, not {priority!r}")
