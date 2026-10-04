"""Reminder data per user: custom_reminders (times the user chose) and reminders_sent (what the job sent)."""
from db import connection


def custom_reminders(user_id):
    # {"2026-10-03": {"remind_at": "20:55", "set_at": "..."}}, the shape the planner reads
    with connection() as conn:
        rows = conn.execute("""SELECT reminder_date, to_char(remind_at, 'HH24:MI') AS remind_at, set_at
                               FROM custom_reminders WHERE user_id = %s""", (user_id,))
        return {row["reminder_date"].isoformat(): {"remind_at": row["remind_at"],
                                                   "set_at": row["set_at"].isoformat(timespec="seconds")}
                for row in rows}


def set_custom(user_id, day, remind_at):
    # Insert, or move the time if this day already has one (the primary key is user + date)
    with connection() as conn:
        conn.execute("""INSERT INTO custom_reminders (user_id, reminder_date, remind_at) VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, reminder_date) DO UPDATE SET remind_at = EXCLUDED.remind_at,
                                                                           set_at = now()""",
                     (user_id, day, remind_at))


def clear_custom(user_id, day):
    with connection() as conn:
        return conn.execute("DELETE FROM custom_reminders WHERE user_id = %s AND reminder_date = %s",
                            (user_id, day)).rowcount > 0


def _sent_json(row):
    return {"status": row["status"], "remind_at": row["remind_at"], "custom": row["custom"], "to": row["to_email"],
            "email_id": row["provider_id"], "error": row["error"],
            "sent_at": row["sent_at"].isoformat(timespec="seconds")}


SENT_SELECT = """SELECT reminder_date, to_char(remind_at, 'HH24:MI') AS remind_at, custom, status, to_email,
                        provider_id, error, sent_at
                 FROM reminders_sent"""


def sent_log(user_id):
    with connection() as conn:
        rows = conn.execute(SENT_SELECT + " WHERE user_id = %s ORDER BY reminder_date", (user_id,))
        return {row["reminder_date"].isoformat(): _sent_json(row) for row in rows}


def sent_on(user_id, day):
    with connection() as conn:
        row = conn.execute(SENT_SELECT + " WHERE user_id = %s AND reminder_date = %s", (user_id, day)).fetchone()
    return _sent_json(row) if row else None


def claim_day(user_id, day, remind_at, custom):
    """Mark the day as "sending" BEFORE the email goes out. Returns True if this call got the claim.

    The primary key (user_id, reminder_date) allows one row per user per day, so if two copies of the
    job try at once, only one INSERT wins. The ON CONFLICT part re-claims a day only when it's a custom
    reminder the user re-timed after it was sent (they asked for it again, at the new time)."""
    with connection() as conn:
        row = conn.execute("""INSERT INTO reminders_sent (user_id, reminder_date, remind_at, custom, status)
                              VALUES (%s, %s, %s, %s, 'sending')
                              ON CONFLICT (user_id, reminder_date) DO UPDATE
                                  SET remind_at = EXCLUDED.remind_at, custom = true, status = 'sending',
                                      provider_id = NULL, error = NULL, sent_at = now()
                                  WHERE EXCLUDED.custom AND reminders_sent.remind_at <> EXCLUDED.remind_at
                              RETURNING 1""", (user_id, day, remind_at, custom)).fetchone()
    return row is not None


def record_sent(user_id, day, result):
    # result: what send_reminder() returned: {"status", "to", "email_id" or "error", ...}
    with connection() as conn:
        conn.execute("""UPDATE reminders_sent SET status = %s, to_email = %s, provider_id = %s, error = %s,
                                                  sent_at = now()
                        WHERE user_id = %s AND reminder_date = %s""",
                     (result["status"], result.get("to"), result.get("email_id"), result.get("error"),
                      user_id, day))
