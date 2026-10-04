"""Matching a schedule location ("Giedt 1002") to a campus building and a room.

Schedule names don't always match the map's names, so we try a few rules in order and
report which one worked. Anything unmatched stays None: the class still gets reminders,
and the user can pick the building by hand.
"""
import re

from parking.data import BUILDINGS
from parking.search import find, search_buildings

ACADEMIC = "Academic & Administration"


def split_room(location):
    # "Storer Hall 1322" → ("Storer Hall", "1322");  "The Grove (Surge III) 1309" → ("The Grove (Surge III)", "1309")
    match = re.fullmatch(r"(.*?)\s+([0-9]{1,4}[A-Z]?)", location.strip())
    return (match[1], match[2]) if match else (location.strip(), None)


def match_building(location):
    """→ (building feature or None, room or None, how it matched)."""
    if not location:
        return None, None, "no location"
    name, room = split_room(location)
    without_brackets = re.sub(r"\s*\(.*?\)", "", name).strip()      # "The Grove (Surge III)" → "The Grove"

    for candidate, how in ((name, "exact name"),
                           (without_brackets, "name without brackets"),
                           (f"{without_brackets} Hall", 'added "Hall"')):    # "Giedt" → "Giedt Hall"
        building = find(BUILDINGS, candidate)
        if building is not None:
            return building, room, how

    # Last try: type-ahead search, but only trust an Academic building that starts with the name
    for building in search_buildings(BUILDINGS, without_brackets, limit=3):
        p = building["properties"]
        if p["type1_name"] == ACADEMIC and p["loc_name"].lower().startswith(without_brackets.lower()):
            return building, room, "search"
    return None, room, "not found"
