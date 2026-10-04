"""Real walking and driving times, and route shapes for the map, from Google's Routes API.

Our own distance is a straight line. Google follows real paths and roads: walks here were
1.3-2.3 times the straight line, so the picks are decided on Google's answers when we have them.

- The API key is read from backend/.env (git-ignored), so it stays on the server.
- Answers are cached in backend/routes_cache.json. A lot-to-building walk never changes, so it
  costs one Google request, ever. Trips from a user's location are cached by position (about 10 m).
- A monthly cap stops calling Google before the free tier runs out.
- If anything fails (no key, no internet, cap reached), callers get nothing back and keep the
  straight-line estimate. A reminder or recommendation never breaks because of Google.
"""
import json
import os
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from parking.data import feature_id
from parking.geo import centre, nearest_corner
from parking.ranking import WALK_METRES_PER_MIN

BACKEND = Path(__file__).resolve().parents[1]     # backend/parking/google_routes.py → backend/
load_dotenv(BACKEND / ".env")                     # puts GOOGLE_MAPS_API_KEY into os.environ
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

MATRIX_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
ROUTE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
CACHE_FILE = BACKEND / "routes_cache.json"
MONTHLY_CAP = 9000                               # stay under Google's 10,000 free requests a month


# --- Links and unit conversion ---

def directions_url(lot):
    # Google Maps turn-by-turn driving directions to the lot: no key, no limit
    lat, lng = centre(lot)
    return f"https://www.google.com/maps/dir/?api=1&destination={lat:.6f},{lng:.6f}&travelmode=driving"


def as_metres(seconds):
    # A real walking time converted to "estimate metres", so pick() (which divides metres
    # by WALK_METRES_PER_MIN) compares real minutes with the walk limit
    return seconds / 60 * WALK_METRES_PER_MIN


# --- Cache (also counts this month's Google usage) ---

def read_cache():
    cache = json.loads(CACHE_FILE.read_text()) if CACHE_FILE.exists() else {}
    for section in ("walks", "drives", "routes", "usage"):
        cache.setdefault(section, {})            # older cache files may lack newer sections
    return cache


def write_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, indent=1))


def can_ask(cache, requests):
    used = cache["usage"].get(date.today().strftime("%Y-%m"), 0)
    return bool(API_KEY) and used + requests <= MONTHLY_CAP


def count(cache, requests):
    month = date.today().strftime("%Y-%m")
    cache["usage"][month] = cache["usage"].get(month, 0) + requests


# --- Talking to Google ---

def post(url, body, field_mask):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": API_KEY,
            "X-Goog-FieldMask": field_mask,      # only the fields we use: Google bills by what you ask for
        },
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.loads(response.read())


def waypoint(lat, lng):
    return {"location": {"latLng": {"latitude": lat, "longitude": lng}}}


def ask_matrix(origins, destinations, mode):
    # One request for every origin-destination pair. Returns {(origin index, destination index): (seconds, metres)}
    body = {
        "origins": [{"waypoint": waypoint(*o)} for o in origins],
        "destinations": [{"waypoint": waypoint(*d)} for d in destinations],
        "travelMode": mode,                       # "WALK" or "DRIVE" (no live traffic: the cheaper tier)
    }
    elements = post(MATRIX_URL, body, "originIndex,destinationIndex,duration,distanceMeters,condition")
    return {
        (e.get("originIndex", 0), e.get("destinationIndex", 0)): (int(e["duration"].rstrip("s")), e.get("distanceMeters", 0))
        for e in elements if e.get("condition") == "ROUTE_EXISTS"      # durations arrive like "534s"
    }


def decode_polyline(encoded):
    # Google squeezes a route's points into a short string ("encoded polyline"); this unpacks
    # it into [[lat, lng], ...] that a map can draw. Each number is stored as the change from
    # the previous point, in 5-bit chunks.
    points, index, lat, lng = [], 0, 0, 0
    while index < len(encoded):
        for axis in (0, 1):
            shift = result = 0
            while True:
                chunk = ord(encoded[index]) - 63
                index += 1
                result |= (chunk & 0x1F) << shift
                shift += 5
                if chunk < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else result >> 1
            if axis == 0:
                lat += delta
            else:
                lng += delta
        points.append([lat / 1e5, lng / 1e5])
    return points


# --- What the rest of the app calls ---

def walk_times(lots, destination_feature, destination_key):
    """Real walks (seconds, metres) from each lot to a destination, by lot OBJECTID.
    destination_key names the destination in the cache, e.g. "b439" for Olson Hall."""
    cache = read_cache()
    found, missing = {}, []
    for lot in lots:
        key = f"{feature_id(lot)}>{destination_key}"
        if key in cache["walks"]:
            found[feature_id(lot)] = tuple(cache["walks"][key])
        else:
            missing.append(lot)
    if missing and can_ask(cache, len(missing)):
        destination = centre(destination_feature)
        try:
            answers = ask_matrix([nearest_corner(lot, destination) for lot in missing], [destination], "WALK")
            count(cache, len(missing))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as error:
            print(f"Routes API failed, using straight-line estimates: {error}")
            answers = {}
        for index, lot in enumerate(missing):
            if (index, 0) in answers:
                found[feature_id(lot)] = answers[(index, 0)]
                cache["walks"][f"{feature_id(lot)}>{destination_key}"] = list(answers[(index, 0)])
        write_cache(cache)
    return found


def real_walks(destination_feature, destination_key, lots_with_metres, walk_limit_min, max_lots=25):
    """Google walks for the lots that could matter, by lot OBJECTID.
    lots_with_metres is a nearest-first list whose items start with straight-line metres and end with the lot.
    Only lots within twice the walk limit (by estimate) are asked about: real walks were at most
    about 2.3x the straight line, so anything further can't be within the limit anyway."""
    candidates = [item[-1] for item in lots_with_metres if item[0] / WALK_METRES_PER_MIN <= 2 * walk_limit_min]
    return walk_times(candidates[:max_lots], destination_feature, destination_key)


def drive_times(origin, origin_key, lots):
    """Real drives (seconds, metres) from a point (lat, lng) to each lot, by lot OBJECTID.
    origin_key names the point in the cache, e.g. "p38.5423,-121.7496"."""
    cache = read_cache()
    found, missing = {}, []
    for lot in lots:
        key = f"{origin_key}>{feature_id(lot)}"
        if key in cache["drives"]:
            found[feature_id(lot)] = tuple(cache["drives"][key])
        else:
            missing.append(lot)
    if missing and can_ask(cache, len(missing)):
        try:
            answers = ask_matrix([origin], [centre(lot) for lot in missing], "DRIVE")
            count(cache, len(missing))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as error:
            print(f"Routes API failed, no driving times: {error}")
            answers = {}
        for index, lot in enumerate(missing):
            if (0, index) in answers:
                found[feature_id(lot)] = answers[(0, index)]
                cache["drives"][f"{origin_key}>{feature_id(lot)}"] = list(answers[(0, index)])
        write_cache(cache)
    return found


def route(start, end, mode, cache_key):
    """One route with its shape, for drawing on the map: {"seconds", "metres", "path": [[lat, lng], ...]},
    or None if Google can't answer."""
    cache = read_cache()
    if cache_key in cache["routes"]:
        return cache["routes"][cache_key]
    if not can_ask(cache, 1):
        return None
    body = {"origin": waypoint(*start), "destination": waypoint(*end), "travelMode": mode}
    try:
        answer = post(ROUTE_URL, body, "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline")
        count(cache, 1)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"Routes API failed, no route to draw: {error}")
        return None
    if not answer.get("routes"):
        return None
    best = answer["routes"][0]
    result = {
        "seconds": int(best["duration"].rstrip("s")),
        "metres": best.get("distanceMeters", 0),
        "path": decode_polyline(best["polyline"]["encodedPolyline"]),
    }
    cache["routes"][cache_key] = result
    write_cache(cache)
    return result
