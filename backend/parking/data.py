"""Campus data: the parking lots and buildings from the UC Davis campus map (data/*.geojson).

Loaded once, when this module is first imported, so the 2 MB building file isn't re-read
on every request. Phase 4 replaces this with database tables.
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"     # backend/parking/data.py → repo/data


def load(filename):
    # Read a GeoJSON file and return its list of features
    with open(DATA / filename) as f:
        return json.load(f)["features"]      # JSON text → Python dicts and lists


BUILDINGS = load("ucd_buildings.geojson")
LOTS = load("ucd_parking_lots.geojson")

# Look-ups by id. OBJECTID is the map service's row number: good enough until the database gives real ids
BUILDINGS_BY_ID = {b["properties"]["OBJECTID"]: b for b in BUILDINGS}
LOTS_BY_ID = {lot["properties"]["OBJECTID"]: lot for lot in LOTS}


def feature_id(feature):
    return feature["properties"]["OBJECTID"]


def lot_label(lot):
    # 71 lots have no name in the source data, so fall back to their map ID
    return lot["properties"]["loc_name"] or f"(unnamed, ID {lot['properties']['OBJECTID']})"


def zone_letter(lot):
    # "C (Visitor) Permit Parking" → "C";  "Misc. Parking Lot" → "?" (no zone, price unknown)
    zone_name = lot["properties"]["type2_name"]
    return zone_name.split()[0] if "Permit Parking" in zone_name else "?"


def is_open(lot):
    # Restricted and Under Construction lots are never recommended
    return lot["properties"]["status"] == "Existing"
