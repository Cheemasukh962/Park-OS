import difflib
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

WALK_METRES_PER_MIN = 80

# 1. LOAD: read a GeoJSON file and return its list of features
def load(filename):
    with open(DATA / filename) as f:
        return json.load(f)["features"]      # JSON text → Python dicts and lists

# 2. FIND: go through the features and return the one with this name (ignoring capitals)
def find(features, name):
    for feature in features:
        loc_name = feature["properties"]["loc_name"] or ""
        if loc_name.lower() == name.lower():
            return feature
    return None

def suggest(features, name):
    # Names that look close to what was typed, e.g. "Olsen Hall" → "Olson Hall"
    names = [f["properties"]["loc_name"] for f in features if f["properties"]["loc_name"]]
    return difflib.get_close_matches(name, names, n=3)

# 3. MEASURE: helper functions for the distance
def corners(geometry):
    # Polygon or MultiPolygon → one flat list of [lng, lat] points
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return [point for polygon in polygons for ring in polygon for point in ring]

def metres_between(a, b):
    # Haversine formula: distance between two lat/lng points on a sphere
    lng1, lat1, lng2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))

def distance(feature_a, feature_b):
    # Closest pair of corners: a rough stand-in for PostGIS's edge-to-edge ST_Distance
    return min(metres_between(a, b) for a in corners(feature_a["geometry"]) for b in corners(feature_b["geometry"]))

def lot_label(lot):
    # 71 lots have no name in the source data, so fall back to their map ID
    return lot["properties"]["loc_name"] or f"(unnamed, ID {lot['properties']['OBJECTID']})"

def zone_letter(lot):
    # "C (Visitor) Permit Parking" → "C";  "Misc. Parking Lot" → "?" (no zone, price unknown)
    zone_name = lot["properties"]["type2_name"]
    return zone_name.split()[0] if "Permit Parking" in zone_name else "?"

# Who may park in which zone (preview of the zone_rates table)
ALLOWED_ZONES = {
    "student": {"C+", "C", "L"},
    "staff":   {"A", "C+", "C", "L"},
    "visitor": {"C", "L"},
}

def can_park(affiliation, zone, hour):
    if affiliation == "student" and zone == "A" and hour >= 17:   # A opens to students at 5pm
        return True
    return zone in ALLOWED_ZONES[affiliation]

# 4. RANK: every open lot this user may park in, nearest first
def nearest_lots(building, lots, affiliation, hour):
    ranked = []
    for lot in lots:
        if lot["properties"]["status"] != "Existing":     # skip Restricted / Under Construction
            continue
        if zone_letter(lot) == "?":                        # skip Misc. lots: unknown price and access
            continue
        if not can_park(affiliation, zone_letter(lot), hour):
            continue
        metres = distance(building, lot)
        ranked.append((metres, lot))
    ranked.sort(key=lambda pair: pair[0])                  # sort by the first item: metres
    return ranked

# 5. RUN
BUILDING_NAME = "Olson Hall"
AFFILIATION = "student"   # "student", "staff" or "visitor"
CLASS_HOUR = 10           # 24-hour clock, so 18 = 6pm

buildings = load("ucd_buildings.geojson")
lots = load("ucd_parking_lots.geojson")

building = find(buildings, BUILDING_NAME)
if building is None:
    print(f'No building called "{BUILDING_NAME}". Did you mean: {suggest(buildings, BUILDING_NAME)}?')
else:
    print(f"Lots near {building['properties']['loc_name']} for a {AFFILIATION} at {CLASS_HOUR}:00:")
    for rank, (metres, lot) in enumerate(nearest_lots(building, lots, AFFILIATION, CLASS_HOUR)[:10], start=1):
        print(f"{rank:>3}. {lot_label(lot):<32} {zone_letter(lot):<3} {metres:>5.0f} m  {metres / WALK_METRES_PER_MIN:>3.0f} min")
