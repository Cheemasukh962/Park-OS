"""Turning an uploaded schedule file into classes the app can save.

    upload (.ics or .pdf) → parser → meetings → match buildings → classes for the user to review

    meetings.py   the shared "meeting" shape, plus day and time conversions
    buildings.py  "Giedt 1002" → the Giedt Hall building + room 1002
    ics.py        calendar files (.ics): structured, so this is exact
    pdf.py        Schedule Builder's printed page (.pdf): messier, read by column and position
    parse.py      picks the right parser for a file and finishes the job

Nothing here saves anything: the user checks the result first (the front end's Grid step).
"""
