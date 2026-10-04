"""ParkOS API server: creates the Flask app and plugs in each group of routes from api/.

Run from the repo root:   .venv\\Scripts\\python backend\\app.py
Then try:                 http://localhost:5000/api/buildings?q=olson
"""
from flask import Flask

from api import buildings, lots, recommendations, reminders, schedule, schedule_import, settings
from api.errors import register_error_handlers


def create_app():
    app = Flask(__name__)
    for module in (buildings, recommendations, schedule, schedule_import, settings, reminders, lots):
        app.register_blueprint(module.bp)        # a Blueprint is a named group of routes
    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5000, debug=True)        # debug: auto-restart when a file changes, detailed errors
