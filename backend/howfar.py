import json
import math

DATA = "C:/Users/Cheem/PARKOS/data/"

# 1. LOAD: read a GeoJSON file and return its list of features
def load(filename):
    with open(DATA + filename) as f:
        return json.load(f)["features"]      # JSON text → Python dicts and lists

# 2. FIND: go through the features and return the one with this name
def find(features, name):
    for feature in features:
        if feature["properties"]["loc_name"] == name:
            return feature
    return None

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

# 4. RUN
building = find(load("ucd_buildings.geojson"), "Olson Hall")
lot = find(load("ucd_parking_lots.geojson"), "Lot 47")

print("Building:", building["properties"]["loc_name"], "| CAAN", building["properties"]["pk_CAAN"])
print("Lot:     ", lot["properties"]["loc_name"], "|", lot["properties"]["type2_name"])

distance = min(metres_between(a, b) for a in corners(building["geometry"]) for b in corners(lot["geometry"]))
print(f"Distance: {distance:.0f} m, about {distance / 80:.0f} min walk")
