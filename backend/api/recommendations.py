"""Lot recommendations and trip routes for the Map page.

GET /api/recommendations   lots for a trip, with Best / Cheapest / Closest picks
GET /api/route             the trip's shape (drive and/or walk legs) for drawing on the map
"""
from datetime import datetime

from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from api.params import building_param, int_param, location_key, location_param
from api.shapes import leg_json, option_json
from api.store import read_store
from parking.data import LOTS, LOTS_BY_ID, feature_id, lot_label, zone_letter
from parking.geo import centre, make_point, nearest_corner
from parking.google_routes import directions_url, drive_times, real_walks, route
from parking.prices import AFFILIATIONS
from parking.ranking import PRIORITIES, nearest_lots
from parking.trips import build_options, pick_trip, total_s

bp = Blueprint("recommendations", __name__)


@bp.get("/api/recommendations")
def recommendations():
    """From a class building (walk), from the user's location (drive), or both
    (drive there, then walk to class). Picks use Google's real times when available."""
    settings = read_store()["settings"]
    affiliation = request.args.get("affiliation", settings["affiliation"])
    if affiliation not in AFFILIATIONS:
        raise BadRequest(f"affiliation must be one of {AFFILIATIONS}")
    hour = int_param("hour", default=datetime.now().hour)
    if not 0 <= hour <= 23:
        raise BadRequest("hour must be 0-23")
    walk_limit = int_param("walk_limit_min", default=settings["walk_limit_min"])
    building, here = building_param(), location_param()
    if building is None and here is None:
        raise BadRequest("send building_id, or lat and lng, or both")

    if building is not None:
        # Rank by distance to class, and get real walks for the lots that could matter
        ranked = nearest_lots(building, LOTS, affiliation, hour)
        walks = real_walks(building, f"b{feature_id(building)}", ranked, walk_limit)
        candidates = [lot for _, _, lot in ranked if feature_id(lot) in walks] or [lot for _, _, lot in ranked[:25]]
    else:
        # Location only: rank by straight-line distance from the user
        ranked = nearest_lots(make_point(*here), LOTS, affiliation, hour)
        walks, candidates = None, [lot for _, _, lot in ranked[:25]]

    drives = drive_times(here, location_key(here), candidates) if here is not None else None

    options = build_options(ranked, walks, drives)
    options.sort(key=total_s)

    # All three picks at once, so the Best / Cheapest / Closest chips switch without another request
    return jsonify({
        "building": building["properties"]["loc_name"] if building else None,
        "from_location": here is not None,
        "affiliation": affiliation,
        "hour": hour,
        "walk_limit_min": walk_limit,
        **{priority: option_json(pick_trip(options, priority, walk_limit)) for priority in PRIORITIES},
        "ranked": [option_json(o) for o in options[:10]],
    })


@bp.get("/api/route")
def trip_route():
    """Drive from the user's location to the lot and/or walk from the lot to the class building.
    Each leg is {"minutes", "metres", "path": [[lat, lng], ...]} for the map to draw."""
    lot = LOTS_BY_ID.get(int_param("lot_id", default=-1))
    if lot is None:
        raise BadRequest("send a lot_id from /api/recommendations")
    building, here = building_param(), location_param()
    if building is None and here is None:
        raise BadRequest("send building_id, or lat and lng, or both")

    drive = walk = None
    if here is not None:
        drive = route(here, centre(lot), "DRIVE", f"drive:{location_key(here)}>{feature_id(lot)}")
    if building is not None:
        destination = centre(building)
        walk = route(nearest_corner(lot, destination), destination, "WALK",
                     f"walk:{feature_id(lot)}>b{feature_id(building)}")

    return jsonify({
        "lot": {"lot_id": feature_id(lot), "lot_name": lot_label(lot), "zone": zone_letter(lot),
                "centre": list(centre(lot)), "directions_url": directions_url(lot)},
        "drive": leg_json(drive),
        "walk": leg_json(walk),
    })
