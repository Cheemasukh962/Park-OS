"""Reading a calendar file (.ics), e.g. Schedule Builder's "export to calendar" (AggieMate).

An .ics file is plain text in a standard format (iCalendar). Each class meeting is a block:

    BEGIN:VEVENT
    SUMMARY:ECS 170 001 Introduction to Artificial Intelligence Lecture
    LOCATION:Teaching and Learning Complex 1010
    DTSTART;TZID=America/Los_Angeles:20261006T164000      ← first class: Oct 6, 16:40
    DTEND;TZID=America/Los_Angeles:20261006T180000
    RRULE:FREQ=WEEKLY;UNTIL=20261215T235959Z;BYDAY=TU,TH  ← repeats every Tue and Thu
    END:VEVENT

Because every field is labelled, this parser is exact. Events that don't repeat weekly
(final exams) are reported as skipped rather than turned into weekly classes.
"""
import re

from schedule_import.meetings import ICS_DAYS, MEETING_TYPES, make_meeting


def unfold(text):
    # Long .ics lines are split with a newline + space; join them back
    return re.sub(r"\r?\n[ \t]", "", text).splitlines()


def unescape(value):
    # .ics escapes commas, semicolons and newlines: "Room 1\, Hall" → "Room 1, Hall"
    return value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def events(lines):
    # Every VEVENT as {"SUMMARY": ..., "DTSTART": ..., ...}
    event = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            event = {}
        elif line == "END:VEVENT" and event is not None:
            yield event
            event = None
        elif event is not None and ":" in line:
            key, value = line.split(":", 1)
            event[key.split(";")[0]] = unescape(value)     # "DTSTART;TZID=..." → "DTSTART"


def split_summary(summary):
    # "ECS 170 001 Introduction to Artificial Intelligence Lecture" → ("ECS", "170", "001", title, "Lecture")
    match = re.fullmatch(r"([A-Z]{2,4})\s+(\d{3}[A-Z]{0,2})\s+(\w{3})\s+(.*)", summary.strip())
    if not match:
        return None
    subject, number, section, rest = match.groups()
    for meeting_type in MEETING_TYPES:
        if rest.endswith(" " + meeting_type) or rest == meeting_type:
            return subject, number, section, rest[: -len(meeting_type)].strip(), meeting_type
    return subject, number, section, rest, None


def clock(value):
    # "20261006T164000" → "16:40"
    match = re.search(r"T(\d\d)(\d\d)", value or "")
    return f"{match[1]}:{match[2]}" if match else None


def parse_ics(text):
    """→ (meetings, skipped). skipped lists what wasn't turned into a weekly class, and why."""
    meetings, skipped = [], []
    for event in events(unfold(text)):
        summary = event.get("SUMMARY", "")
        parts = split_summary(summary)
        if parts is None:
            skipped.append({"text": summary, "reason": "not a course (no course code)"})
            continue
        if "FREQ=WEEKLY" not in event.get("RRULE", ""):
            skipped.append({"text": summary, "reason": "one-time event (e.g. a final exam)"})
            continue
        byday = re.search(r"BYDAY=([A-Z,]+)", event["RRULE"])
        days = sorted({ICS_DAYS[d] for d in byday[1].split(",") if d in ICS_DAYS}) if byday else []
        subject, number, section, title, meeting_type = parts
        meetings.append(make_meeting(subject, number, section, meeting_type, days,
                                     clock(event.get("DTSTART")), clock(event.get("DTEND")),
                                     event.get("LOCATION"), title=title))
    return meetings, skipped
