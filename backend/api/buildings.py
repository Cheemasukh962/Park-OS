"""GET /api/buildings?q=well: type-ahead building search."""
from flask import Blueprint, jsonify, request

from api.shapes import building_json
from parking.data import BUILDINGS
from parking.search import search_buildings

bp = Blueprint("buildings", __name__)


@bp.get("/api/buildings")
def buildings():
    query = request.args.get("q", "")            # reads ?q=well from the URL
    return jsonify([building_json(b) for b in search_buildings(BUILDINGS, query)])
