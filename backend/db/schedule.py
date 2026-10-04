"""Each user's classes: the schedule_entries table.

Rows come back in the same shape the API always used:
{"id", "course", "days": [1, 3], "start": "HH:MM", "end": "HH:MM" or None, "building_id"}
Every query includes user_id, so a user can only ever read or change their own classes.
"""
from db import connection

SELECT = """SELECT id, course, days, to_char(start_time, 'HH24:MI') AS start,
                   to_char(end_time, 'HH24:MI') AS "end", building_id
            FROM schedule_entries"""


def list_entries(user_id):
    with connection() as conn:
        return conn.execute(SELECT + " WHERE user_id = %s ORDER BY id", (user_id,)).fetchall()


def _insert(conn, user_id, entry):
    row = conn.execute("""INSERT INTO schedule_entries (user_id, course, days, start_time, end_time, building_id)
                          VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                       (user_id, entry["course"], entry["days"], entry["start"], entry["end"],
                        entry["building_id"])).fetchone()
    return {"id": row["id"], **entry}


def add_entry(user_id, entry):
    with connection() as conn:
        return _insert(conn, user_id, entry)


def replace_entries(user_id, entries):
    # One transaction: the old classes are deleted and the new ones added together, or not at all
    with connection() as conn:
        conn.execute("DELETE FROM schedule_entries WHERE user_id = %s", (user_id,))
        return [_insert(conn, user_id, entry) for entry in entries]


def update_entry(user_id, entry_id, entry):
    """Returns the updated class, or None if this user has no class with that id."""
    with connection() as conn:
        found = conn.execute("""UPDATE schedule_entries SET course = %s, days = %s, start_time = %s,
                                       end_time = %s, building_id = %s
                                WHERE id = %s AND user_id = %s RETURNING id""",
                             (entry["course"], entry["days"], entry["start"], entry["end"], entry["building_id"],
                              entry_id, user_id)).fetchone()
    return {"id": entry_id, **entry} if found else None


def delete_entry(user_id, entry_id):
    with connection() as conn:
        return conn.execute("DELETE FROM schedule_entries WHERE id = %s AND user_id = %s",
                            (entry_id, user_id)).rowcount > 0
