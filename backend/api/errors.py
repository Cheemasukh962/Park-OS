"""Errors: always answer in JSON, never Flask's default HTML page, so the front end can show the message."""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class BadRequest(Exception):
    # Raised anywhere in a route when the request is wrong: becomes {"error": "..."} with status 400
    pass


def register_error_handlers(app):
    @app.errorhandler(BadRequest)
    def bad_request(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(HTTPException)
    def http_error(error):                       # 404 Not Found, 405 Method Not Allowed, ...
        return jsonify({"error": error.description}), error.code
