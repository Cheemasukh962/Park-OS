"""Geometry helpers: points, corners and straight-line distance.

GeoJSON stores coordinates as [longitude, latitude] (longitude first). Functions here that
take or return a plain point use (lat, lng), the order people and Google use, and say so.
"""
import math

CAMPUS_CENTRE = (38.5382, -121.7617)          # (lat, lng), roughly the Quad


def make_point(lat, lng):
    # The user's location from the browser, shaped like a GeoJSON feature so the
    # same distance code works for "from a building" and "from where I am"
    return {"type": "Feature", "properties": {"loc_name": "Your location"},
            "geometry": {"type": "Point", "coordinates": [lng, lat]}}   # GeoJSON is [lng, lat]


def corners(geometry):
    # Point, Polygon or MultiPolygon → one flat list of [lng, lat] points
    if geometry["type"] == "Point":
        return [geometry["coordinates"]]
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    return [point for polygon in polygons for ring in polygon for point in ring]


def metres_between(a, b):
    # Haversine formula: distance between two [lng, lat] points on a sphere
    lng1, lat1, lng2, lat2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def distance(feature_a, feature_b):
    # Closest pair of corners: a rough stand-in for PostGIS's edge-to-edge ST_Distance
    return min(metres_between(a, b) for a in corners(feature_a["geometry"]) for b in corners(feature_b["geometry"]))


def centre(feature):
    # Average of the corners, as (lat, lng)
    points = corners(feature["geometry"])
    return sum(p[1] for p in points) / len(points), sum(p[0] for p in points) / len(points)


def nearest_corner(feature, target):
    # The corner of a shape closest to a (lat, lng) target, as (lat, lng):
    # roughly where you'd walk out of a lot towards your class
    lng, lat = min(corners(feature["geometry"]), key=lambda p: metres_between(p, [target[1], target[0]]))
    return lat, lng


def km_from_campus(point):
    # A (lat, lng) point's straight-line distance from campus, in km
    return metres_between([point[1], point[0]], [CAMPUS_CENTRE[1], CAMPUS_CENTRE[0]]) / 1000
