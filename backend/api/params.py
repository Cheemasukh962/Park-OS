"""Reading and checking query parameters (?building_id=439&lat=...). Never trust what the browser sends."""
from flask import request

from api.errors import BadRequest
from parking.data import BUILDINGS_BY_ID


def int_param(name, default=None):
    value = request.args.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise BadRequest(f"{name} must be a whole number")


def building_param():
    # ?building_id=439 → the building feature, or None if not sent
    building_id = int_param("building_id")
    if building_id is None:
        return None
    if building_id not in BUILDINGS_BY_ID:
        raise BadRequest("building_id not found (use /api/buildings?q=... to look it up)")
    return BUILDINGS_BY_ID[building_id]


def location_param():
    # ?lat=38.54&lng=-121.75 → (lat, lng), or None if not sent
    lat, lng = request.args.get("lat"), request.args.get("lng")
    if lat is None and lng is None:
        return None
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        raise BadRequest("lat and lng must both be numbers")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise BadRequest("lat must be -90 to 90 and lng -180 to 180")
    return lat, lng


def location_key(point):
    # Rounded to 4 decimals (about 10 m), so nearby requests share cached Google answers
    return f"p{point[0]:.4f},{point[1]:.4f}"
