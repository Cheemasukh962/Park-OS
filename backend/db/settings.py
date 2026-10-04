"""Each user's settings: the user_settings table (one row per user)."""
from psycopg import sql

from db import connection

COLUMNS = ("affiliation", "lead_minutes", "walk_limit_min", "priority", "reminders_enabled", "channel", "email")


def _shape(row):
    # The API sends "" for "no email yet"; the database stores that as NULL
    return {**row, "email": row["email"] or ""}


def get_settings(user_id):
    with connection() as conn:
        row = conn.execute(sql.SQL("SELECT {} FROM user_settings WHERE user_id = %s").format(
            sql.SQL(", ").join(map(sql.Identifier, COLUMNS))), (user_id,)).fetchone()
    return _shape(row)


def update_settings(user_id, changes):
    """changes: {column: value}, already checked by the API. Returns the full settings after saving."""
    # Column names can't be %s placeholders, so they're added as quoted identifiers, and only
    # from the fixed COLUMNS list: nothing the browser sends ever becomes SQL text
    changes = {key: (None if key == "email" and value == "" else value)
               for key, value in changes.items() if key in COLUMNS}
    if changes:
        assignments = sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(key)) for key in changes)
        with connection() as conn:
            conn.execute(sql.SQL("UPDATE user_settings SET {} WHERE user_id = %s").format(assignments),
                         (*changes.values(), user_id))
    return get_settings(user_id)


def users_with_reminders():
    # Everyone the reminder job should check: reminders on and an email to send to
    with connection() as conn:
        rows = conn.execute("SELECT user_id FROM user_settings WHERE reminders_enabled AND email IS NOT NULL")
        return [row["user_id"] for row in rows]
