"""Accounts: the users table, plus the user_settings row every new account starts with."""
from psycopg.errors import UniqueViolation

from db import connection


def create_user(email, password_hash):
    """Returns the new user's id, or None if that email (ignoring capitals) already has an account."""
    try:
        with connection() as conn:
            user_id = conn.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                                   (email, password_hash)).fetchone()["id"]
            # Reminders go to the sign-in email unless the user changes it
            conn.execute("INSERT INTO user_settings (user_id, email) VALUES (%s, %s)", (user_id, email))
            return user_id
    except UniqueViolation:                       # the unique index on lower(email) refused it
        return None


def user_by_email(email):
    with connection() as conn:
        return conn.execute("SELECT id, email, password_hash FROM users WHERE lower(email) = lower(%s)",
                            (email,)).fetchone()


def user_by_id(user_id):
    with connection() as conn:
        return conn.execute("SELECT id, email FROM users WHERE id = %s", (user_id,)).fetchone()
