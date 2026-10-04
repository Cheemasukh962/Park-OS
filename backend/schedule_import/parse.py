"""The import pipeline's front door: file in, classes for the user to review out."""
from schedule_import.buildings import match_building
from schedule_import.ics import parse_ics
from schedule_import.pdf import parse_pdf


class UnsupportedFile(Exception):
    pass


def detect(filename, data):
    # Trust the file's contents over its name: .ics files start with BEGIN:VCALENDAR, PDFs with %PDF
    head = data[:2048].lstrip()
    if head.startswith(b"%PDF"):
        return "pdf"
    if b"BEGIN:VCALENDAR" in head:
        return "ics"
    raise UnsupportedFile(f"{filename or 'this file'} isn't a calendar (.ics) or PDF file")


def to_class(meeting):
    # A parsed meeting → the shape POST /api/schedule saves, plus extra fields to help the user review it
    building, room, how = match_building(None if meeting["online"] else meeting["location"])
    return {
        "course": f"{meeting['course']} {meeting['type'] or ''}".strip(),   # "ECS 170 Lecture"
        "days": meeting["days"],
        "start": meeting["start"],
        "end": meeting["end"],
        "building_id": building["properties"]["OBJECTID"] if building else None,
        # For review only (not saved):
        "building_name": building["properties"]["loc_name"] if building else None,
        "room": room,
        "location": meeting["location"],
        "building_match": how,
        "online": meeting["online"],
        "registered": meeting["registered"],
        # Ticked by default unless it's online (no parking) or the PDF says not registered
        "include": not meeting["online"] and meeting["registered"] is not False,
    }


def import_schedule(filename, data):
    """→ {"source": "ics" | "pdf", "classes": [...], "skipped": [...]}. Saves nothing."""
    source = detect(filename, data)
    if source == "ics":
        meetings, skipped = parse_ics(data.decode("utf-8", errors="replace"))
    else:
        meetings, skipped = parse_pdf(data)
    return {"source": source, "classes": [to_class(m) for m in meetings], "skipped": skipped}
