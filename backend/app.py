"""ParkOS API server: creates the Flask app and plugs in each group of routes from api/.

Run from the repo root:   .venv\\Scripts\\python backend\\app.py
Then try:                 http://localhost:5000/api/buildings?q=olson
"""
import os
import secrets
from datetime import timedelta

from flask import Flask

import config
from api import auth, buildings, lots, recommendations, reminders, schedule, schedule_import, settings
from api.errors import register_error_handlers
from db.migrate import ensure_schema


def create_app():
    app = Flask(__name__)
    if not config.SECRET_KEY:
        print("[app] SECRET_KEY not set: using a random one, so restarting signs everyone out", flush=True)
    app.config.update(
        SECRET_KEY=config.SECRET_KEY or secrets.token_hex(32),
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),      # "Keep me signed in" lasts 30 days
        SESSION_COOKIE_HTTPONLY=True,                      # page scripts can't read the cookie
        SESSION_COOKIE_SAMESITE="Lax",                     # not sent with requests started by other sites
        SESSION_COOKIE_SECURE=config.ON_RAILWAY,           # HTTPS only when deployed (localhost is plain HTTP)
    )
    for module in (auth, buildings, recommendations, schedule, schedule_import, settings, reminders, lots):
        app.register_blueprint(module.bp)        # a Blueprint is a named group of routes
    app.before_request(auth.require_login)       # every /api/ route except sign-in and campus data needs a user
    register_error_handlers(app)
    return app


ensure_schema()                                  # creates the tables the first time, does nothing after
app = create_app()

# On Railway, gunicorn imports this file once, so start the job here
if config.ON_RAILWAY:
    from jobs import reminder_job
    reminder_job.start()

if __name__ == "__main__":
    # In debug mode Flask runs this file twice: a watcher process, and the real server (which has
    # WERKZEUG_RUN_MAIN set). Start the reminder job only in the real server, or it would run twice.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from jobs import reminder_job
        reminder_job.start()
    app.run(port=5000, debug=True)        # debug: auto-restart when a file changes, detailed errors
