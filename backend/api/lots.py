"""GET /api/lots: every lot outline as GeoJSON, for drawing on the map (coloured by zone)."""
from flask import Blueprint, jsonify

from parking.data import LOTS, feature_id, lot_label, zone_letter

bp = Blueprint("lots", __name__)


@bp.get("/api/lots")
def lots_geojson():
    features = [{
        "type": "Feature",
        "geometry": lot["geometry"],
        "properties": {"id": feature_id(lot), "name": lot_label(lot),
                       "zone": zone_letter(lot), "status": lot["properties"]["status"]},
    } for lot in LOTS]
    return jsonify({"type": "FeatureCollection", "features": features})
