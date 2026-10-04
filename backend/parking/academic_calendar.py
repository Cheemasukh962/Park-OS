"""The academic calendar: which dates get reminders (later: the terms and closures tables).

Fall 2026, from the UC Davis Registrar (registrar.ucdavis.edu/calendar/quarter):
instruction Wed Sep 23 - Fri Dec 4; finals Mon Dec 7 - Fri Dec 11 (no regular classes, so no
reminders: final exams are one-time events at different times and places).
"""
from datetime import date

from config import TEST_WEEKENDS

TERM_START = date(2026, 9, 23)        # instruction begins
TERM_END = date(2026, 12, 4)          # instruction ends
FINALS_END = date(2026, 12, 11)       # finals week: no regular classes
CLOSURES = {
    date(2026, 11, 11): "Veterans Day",
    date(2026, 11, 26): "Thanksgiving",
    date(2026, 11, 27): "Thanksgiving break",
}


def skip_reason(day):
    # Why there's no reminder on this date, or None if it's a normal school day
    if TERM_END < day <= FINALS_END:
        return "finals week"
    if not (TERM_START <= day <= TERM_END):
        return "outside the quarter"
    if day.isoweekday() >= 6 and not TEST_WEEKENDS:   # 6 = Saturday, 7 = Sunday (TEST_WEEKENDS: see config.py)
        return "weekend"
    if day in CLOSURES:
        return CLOSURES[day]
    return None
