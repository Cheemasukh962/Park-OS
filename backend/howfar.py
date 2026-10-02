import csv
import difflib
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

WALK_METRES_PER_MIN = 80
WALK_LIMIT_MIN = 10        # default walk limit (later: users.walk_limit_min)

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

# PRICES: read data/zone_rates.csv (preview of the zone_rates table)
def load_rates():
    # {("C", "student"): (550, 0), ("A", "student"): (650, 17), ...}
    rates = {}
    with open(DATA / "zone_rates.csv") as f:
        for row in csv.DictReader(f):                      # each row becomes a dict keyed by the header
            from_hour = int(row["available_from"][:2]) if row["available_from"] else 0   # "17:00" → 17
            rates[(row["zone_code"], row["affiliation"])] = (int(row["price_cents"]), from_hour)
    return rates

RATES = load_rates()

def price_for(zone, affiliation, hour):
    # The price in cents, or None if this user can't park in this zone at this hour.
    # No row in the table means not allowed, which also rules out Misc. lots ("?").
    rate = RATES.get((zone, affiliation))
    if rate is None:
        return None
    price_cents, from_hour = rate
    return price_cents if hour >= from_hour else None

def dollars(cents):
    return f"${cents / 100:.2f}"                           # 375 → "$3.75"

# 4. RANK: every open lot this user may park in, nearest first
def nearest_lots(building, lots, affiliation, hour):
    ranked = []
    for lot in lots:
        if lot["properties"]["status"] != "Existing":     # skip Restricted / Under Construction
            continue
        price = price_for(zone_letter(lot), affiliation, hour)
        if price is None:
            continue
        metres = distance(building, lot)
        ranked.append((metres, price, lot))
    ranked.sort(key=lambda item: item[0])                  # sort by the first item: metres
    return ranked

def cheapest_within(ranked, walk_limit_min):
    # Cheapest lot within the walk limit; ties go to the shorter walk
    nearby = [item for item in ranked if item[0] / WALK_METRES_PER_MIN <= walk_limit_min]
    if not nearby:
        return None
    return min(nearby, key=lambda item: (item[1], item[0]))   # compare price first, then metres

# 5. RUN (only when this file is run directly, not when another file imports it)
if __name__ == "__main__":
    BUILDING_NAME = "Olson Hall"
    AFFILIATION = "student"   # "student", "staff" or "visitor"
    CLASS_HOUR = 10           # 24-hour clock, so 18 = 6pm

    buildings = load("ucd_buildings.geojson")
    lots = load("ucd_parking_lots.geojson")

    building = find(buildings, BUILDING_NAME)
    if building is None:
        print(f'No building called "{BUILDING_NAME}". Did you mean: {suggest(buildings, BUILDING_NAME)}?')
    else:
        ranked = nearest_lots(building, lots, AFFILIATION, CLASS_HOUR)

        print(f"Lots near {building['properties']['loc_name']} for a {AFFILIATION} at {CLASS_HOUR}:00:")
        for rank, (metres, price, lot) in enumerate(ranked[:10], start=1):
            print(f"{rank:>3}. {lot_label(lot):<32} {zone_letter(lot):<3} {dollars(price):>6}  {metres:>5.0f} m  {metres / WALK_METRES_PER_MIN:>3.0f} min")

        closest = ranked[0]
        cheapest = cheapest_within(ranked, WALK_LIMIT_MIN)
        print()
        print(f"Closest:  {lot_label(closest[2])} ({zone_letter(closest[2])}, {dollars(closest[1])}), {closest[0] / WALK_METRES_PER_MIN:.0f} min walk")
        if cheapest:
            saving = closest[1] - cheapest[1]
            print(f"Cheapest within {WALK_LIMIT_MIN} min: {lot_label(cheapest[2])} ({zone_letter(cheapest[2])}, {dollars(cheapest[1])}), "
                  f"{cheapest[0] / WALK_METRES_PER_MIN:.0f} min walk, saves {dollars(saving)} a day")
 