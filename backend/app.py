"""ParkOS API server: creates the Flask app and plugs in each group of routes from api/.

Run from the repo root:   .venv\\Scripts\\python backend\\app.py
Then try:                 http://localhost:5000/api/buildings?q=olson
"""
import os

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
    # In debug mode Flask runs this file twice: a watcher process, and the real server (which has
    # WERKZEUG_RUN_MAIN set). Start the reminder job only in the real server, or it would run twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from jobs import reminder_job
        reminder_job.start()
    app.run(port=5000, debug=True)        # debug: auto-restart when a file changes, detailed errors
