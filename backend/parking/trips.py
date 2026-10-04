"""Picking a lot for a whole trip: drive from where you are, then walk to class.

    your location ──drive──► parking lot ──walk──► class building

Either leg can be missing: no building means drive only, no location means walk only
(the original building-based recommendation). The rules are kept simple on purpose, and
the numbers to tune are the constants below.
"""
from parking.data import feature_id
from parking.ranking import WALK_METRES_PER_MIN

# Location only (no class building): "Best" is the cheapest lot whose drive is at most
# this many minutes longer than the fastest drive. Bigger = more willing to drive for a saving.
DRIVE_SLACK_MIN = 5


def build_options(ranked, walks=None, drives=None):
    """One option per lot: price plus whatever we know about each leg (seconds and metres).

    ranked: nearest_lots() output, (straight-line metres, price, lot)
    walks:  Google walks by lot id, or None when there's no class building
    drives: Google drives by lot id, or None when there's no user location
    """
    options = []
    for metres, price, lot in ranked:
        lot_id = feature_id(lot)
        option = {"lot": lot, "price": price, "walk_s": None, "walk_m": None, "walk_source": None,
                  "drive_s": None, "drive_m": None}
        if walks is not None:
            if lot_id in walks:
                option["walk_s"], option["walk_m"] = walks[lot_id]
                option["walk_source"] = "google"
            else:   # straight-line estimate (Google didn't answer, or the lot was too far to ask about)
                option["walk_s"], option["walk_m"] = metres / WALK_METRES_PER_MIN * 60, metres
                option["walk_source"] = "estimate"
        if drives is not None and lot_id in drives:
            option["drive_s"], option["drive_m"] = drives[lot_id]
        options.append(option)

    # With a location, keep only lots Google gave a drive for (they're the ones near the destination).
    # If Google gave no drives at all (no key, offline), fall back to walk-only ranking.
    if drives:
        options = [o for o in options if o["drive_s"] is not None]
    return options


def total_s(option):
    return (option["drive_s"] or 0) + (option["walk_s"] or 0)


def pick_trip(options, priority, walk_limit_min):
    """One option for "best", "cheapest" or "closest" (closest = shortest whole trip)."""
    if not options:
        return None
    if priority == "closest":
        return min(options, key=total_s)
    if priority == "cheapest":
        return min(options, key=lambda o: (o["price"], total_s(o)))
    if priority == "best":
        if any(o["walk_s"] is not None for o in options):
            # Has a class building: the walk must be within the limit
            pool = [o for o in options if o["walk_s"] is not None and o["walk_s"] <= walk_limit_min * 60]
        else:
            # Location only: drives within DRIVE_SLACK_MIN of the fastest
            fastest = min(o["drive_s"] for o in options if o["drive_s"] is not None)
            pool = [o for o in options if o["drive_s"] <= fastest + DRIVE_SLACK_MIN * 60]
        if pool:
            return min(pool, key=lambda o: (o["price"], total_s(o)))
        return min(options, key=total_s)              # nothing qualifies: the fastest trip
    raise ValueError(f"priority must be best, cheapest or closest, not {priority!r}")
