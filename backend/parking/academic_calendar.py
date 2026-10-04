"""The academic calendar: which dates get reminders (later: the terms and closures tables).

PLACEHOLDER dates: check them against the UC Davis academic calendar.
"""
from datetime import date

TERM_START = date(2026, 9, 23)
TERM_END = date(2026, 12, 11)
CLOSURES = {
    date(2026, 11, 11): "Veterans Day",
    date(2026, 11, 26): "Thanksgiving",
    date(2026, 11, 27): "Thanksgiving break",
}


def skip_reason(day):
    # Why there's no reminder on this date, or None if it's a normal school day
    if not (TERM_START <= day <= TERM_END):
        return "outside the quarter"
    if day.isoweekday() >= 6:              # 6 = Saturday, 7 = Sunday
        return "weekend"
    if day in CLOSURES:
        return CLOSURES[day]
    return None
