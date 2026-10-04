"""Accounts: sign up, sign in, sign out, and who is signed in.

POST /api/auth/signup   {"email", "password", "remember"}  → 201 {"id", "email"}, and signs you in
POST /api/auth/login    {"email", "password", "remember"}  → {"id", "email"}
POST /api/auth/logout                                      → 204
GET  /api/auth/me                                          → {"id", "email"}, or 401 if not signed in

How staying signed in works: after a correct password, Flask puts {"user_id": 7} in the session
cookie and signs it with SECRET_KEY. The browser sends the cookie back with every request; a cookie
that was edited fails the signature check and is ignored, so nobody can pretend to be user 8.
The password is never stored: only werkzeug's scrypt hash, which can check it but not reveal it.
"""
import re

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from api.errors import BadRequest
from db.users import create_user, user_by_email, user_by_id

bp = Blueprint("auth", __name__)

EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")       # same rule as the database's CHECK
MIN_PASSWORD = 8

# Routes anyone may use without signing in: campus data, and signing in itself
PUBLIC = ("/api/auth/", "/api/buildings", "/api/lots")


def current_user_id():
    # The signed-in user, set by require_login() before the route runs
    return g.user_id


def require_login():
    """Runs before every request (registered in app.py). Every /api/ route except PUBLIC needs a
    signed-in user, and every query those routes make uses that user's id."""
    if not request.path.startswith("/api/") or request.path.startswith(PUBLIC):
        return None
    user_id = session.get("user_id")
    if user_id is None or user_by_id(user_id) is None:        # also catches an account that no longer exists
        session.clear()
        return jsonify({"error": "please sign in"}), 401
    g.user_id = user_id
    return None


def read_credentials():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip()
    password = body.get("password")
    if not EMAIL.fullmatch(email) or len(email) > 254:
        raise BadRequest("enter a valid email address")
    if not isinstance(password, str) or not password:
        raise BadRequest("enter your password")
    return email, password, bool(body.get("remember", True))


def sign_in(user_id, email, remember):
    session.clear()                         # a fresh session, so nothing from before carries over
    session["user_id"] = user_id
    session.permanent = remember            # permanent: kept for 30 days; otherwise until the browser closes
    return {"id": user_id, "email": email}


@bp.post("/api/auth/signup")
def signup():
    email, password, remember = read_credentials()
    if not MIN_PASSWORD <= len(password) <= 128:
        raise BadRequest(f"use a password of at least {MIN_PASSWORD} characters")
    user_id = create_user(email, generate_password_hash(password))
    if user_id is None:
        return jsonify({"error": "an account with this email already exists: sign in instead"}), 409
    return jsonify(sign_in(user_id, email, remember)), 201


@bp.post("/api/auth/login")
def login():
    email, password, remember = read_credentials()
    user = user_by_email(email)
    # Same message whether the email or the password was wrong, so the form can't be used to
    # find out which emails have accounts
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "wrong email or password"}), 401
    return jsonify(sign_in(user["id"], user["email"], remember))


@bp.post("/api/auth/logout")
def logout():
    session.clear()
    return "", 204


@bp.get("/api/auth/me")
def me():
    user_id = session.get("user_id")
    user = user_by_id(user_id) if user_id is not None else None
    if user is None:
        return jsonify({"error": "not signed in"}), 401
    return jsonify({"id": user["id"], "email": user["email"]})
