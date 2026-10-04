"""The shared shape every parser produces, plus day and time conversions.

A meeting is one row of a schedule, e.g. ECS 170's Lecture on Tue/Thu 16:40-18:00 in
"Teaching and Learning Complex 1010". One course can have several (lecture, discussion, lab).
"""
import re

# Schedule Builder writes days as letters: R is Thursday, so "TR" = Tue + Thu.
DAY_LETTERS = {"M": 1, "T": 2, "W": 3, "R": 4, "F": 5, "S": 6, "U": 7}
ICS_DAYS = {"MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 7}

# Meeting types, longest first so "Lecture/Discussion" wins over "Lecture"
MEETING_TYPES = ["World Wide Web Virtual Lecture", "Lecture/Discussion", "Independent Study", "Final Exam",
                 "Laboratory", "Discussion", "Fieldwork", "Tutorial", "Lecture", "Seminar", "Studio", "Lab"]

ONLINE_LOCATIONS = {"online learning activity", "online", "remote", "tba"}


def days_from_letters(letters):
    # "MWF" → [1, 3, 5]
    return sorted({DAY_LETTERS[ch] for ch in letters if ch in DAY_LETTERS})


def to_24h(text):
    # "4:40 PM" → "16:40",  "12:10 PM" → "12:10",  "10:00 AM" → "10:00"
    match = re.fullmatch(r"\s*(\d{1,2}):(\d\d)\s*([AP])\.?M\.?\s*", text, re.IGNORECASE)
    if not match:
        return None
    hour, minute, half = int(match[1]), int(match[2]), match[3].upper()
    if half == "P" and hour != 12:
        hour += 12
    if half == "A" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def is_online(meeting_type, location):
    # Online classes don't need parking, so they never get a reminder
    return "virtual" in (meeting_type or "").lower() or (location or "").strip().lower() in ONLINE_LOCATIONS


def make_meeting(subject, number, section, meeting_type, days, start, end, location, title=None, registered=None):
    return {
        "course": f"{subject} {number}",       # "ECS 170"
        "section": section,                    # "001"
        "title": title,                        # "Introduction to Artificial Intelligence" (if known)
        "type": meeting_type,                  # "Lecture"
        "days": days,                          # [2, 4]
        "start": start,                        # "16:40"
        "end": end,                            # "18:00"
        "location": location,                  # "Teaching and Learning Complex 1010"
        "online": is_online(meeting_type, location),
        "registered": registered,              # True / False from the PDF; None when unknown (.ics)
    }
