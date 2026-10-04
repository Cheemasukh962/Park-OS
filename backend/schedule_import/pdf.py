"""Reading Schedule Builder's printed page (.pdf).

A PDF has no labelled fields, only text placed at positions, so this works from the layout:

1. Extract each page's text keeping positions (pypdf "layout" mode), so the two columns of
   course cards stay apart.
2. Find the blank gutter between the columns, and read each column down through ALL pages:
   a card that starts at the bottom of page 1 continues at the top of page 2 in the same column.
3. A course header ("ECS 170 001 Introduction to ...") starts a card; time rows under it
   ("Lecture   4:40 PM - 6:00 PM   TR   Teaching and Learning Complex 1010") are its meetings.
4. Narrow table cells wrap onto the next line ("6:00 P" / "M", "T" / "R", "101" / "0"), so
   fragments on the following lines are glued back onto the field they sit under.

This is tuned to Schedule Builder's print layout. A different layout may need the AI fallback.
"""
import io
import re
import unicodedata

from pypdf import PdfReader

from schedule_import.meetings import days_from_letters, make_meeting, to_24h

HEADER = re.compile(r"([A-Z]{2,4}) (\d{3}[A-Z]{0,2}) (\d{3}) (.+)")
TIME = r"\d{1,2}:\d\d [AP]M? ?- ?\d{1,2}:\d\d ?[AP]?M?"
ROW = re.compile(rf"(?P<type>[A-Za-z/ ]+?)\s{{2,}}(?P<time>{TIME})(?:\s{{2,}}(?P<days>[MTWRFSU]{{1,7}}))?(?:\s{{2,}}(?P<location>.+))?")


def page_lines(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    for page in reader.pages:
        text = unicodedata.normalize("NFKC", page.extract_text(extraction_mode="layout"))   # "ﬁ" → "fi"
        yield text.splitlines()


def gutter(lines):
    # The character position between the two columns: the spot in the middle third of the
    # page where the fewest lines have text on both sides of it
    width = max((len(line) for line in lines), default=0)
    def blocked(c):
        return sum(1 for line in lines if line[c - 1:c + 1].strip())
    return min(range(width // 3, 2 * width // 3), key=blocked, default=width)


def columns(pdf_bytes):
    # Left column of every page, then right column of every page: each reads like one long card list
    left, right = [], []
    for lines in page_lines(pdf_bytes):
        split = gutter(lines)
        left += [line[:split].rstrip() for line in lines]
        right += [line[split:].rstrip() for line in lines]
    return [left, right]


def glue(value, fragment):
    # Join a wrapped fragment back on: no space if a word or number was cut ("Discussio"+"n", "101"+"0", "P"+"M")
    if not value:
        return fragment
    cut = value[-1].isalnum() and (fragment[0].islower() or fragment[0].isdigit() or len(fragment) <= 2)
    return value + ("" if cut else " ") + fragment


def read_row(lines, index):
    """Parse the time row at lines[index], gluing on wrapped fragments from the lines below it."""
    line = lines[index]
    match = ROW.search(line)
    fields = {name: (match.start(name), (match.group(name) or "").strip())
              for name in ("type", "time", "days", "location") if match.start(name) != -1}
    # Where each field starts on the line, so fragments below can be assigned by position
    starts = sorted((pos, name) for name, (pos, _) in fields.items())
    values = {name: value for name, (_, value) in fields.items()}

    for below in lines[index + 1:index + 3]:                 # wrapped cells spill over 1-2 lines at most
        if not below.strip() or ROW.search(below) or HEADER.search(below.strip()):
            break
        for fragment in re.finditer(r"\S+(?: \S+)*", below):
            name = next((n for pos, n in reversed(starts) if pos <= fragment.start() + 2), starts[0][1])
            values[name] = glue(values.get(name, ""), fragment.group())
    # A day letter can end up in the location column when the days cell was empty on the first line
    if not values.get("days") and values.get("location", "").split(" ")[0].isupper():
        first, _, rest = values["location"].partition(" ")
        if set(first) <= set("MTWRFSU"):
            values["days"], values["location"] = first, rest
    return values


def parse_pdf(pdf_bytes):
    """→ (meetings, skipped)."""
    meetings, skipped = [], []
    for lines in columns(pdf_bytes):
        course = None
        for index, line in enumerate(lines):
            text = line.strip()
            header = HEADER.match(text)
            if header and not ROW.search(line):
                subject, number, section, rest = header.groups()
                title = re.split(r"\s{2,}", rest)[0]              # stop at the "Instructor(s):" column
                course = {"subject": subject, "number": number, "section": section, "title": title, "registered": None}
                continue
            if course is None:
                continue
            if text in ("Registered", "Not Registered"):
                course["registered"] = text == "Registered"
                continue
            if ROW.search(line):
                row = read_row(lines, index)
                start_end = re.split(r"\s*-\s*", row["time"])
                start, end = to_24h(start_end[0]), to_24h(start_end[1]) if len(start_end) > 1 else None
                days = days_from_letters(row.get("days", ""))
                if not (start and days):
                    skipped.append({"text": text, "reason": "couldn't read the time or days"})
                    continue
                meeting_type = row["type"].strip()
                meetings.append(make_meeting(course["subject"], course["number"], course["section"], meeting_type,
                                             days, start, end, row.get("location") or None,
                                             title=course["title"], registered=course["registered"]))
    return meetings, skipped
