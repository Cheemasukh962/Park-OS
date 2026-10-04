"""Finding buildings by name: exact look-ups, typo suggestions, and type-ahead search."""
import difflib

# Academic buildings first: that's where classes are. "Other" is mostly sheds and greenhouses.
CATEGORY_ORDER = ["Academic & Administration", "Athletics & Recreation", "Housing & Dining", "Support", "Other"]


def find(features, name):
    # The first feature with exactly this name, ignoring capitals
    for feature in features:
        loc_name = feature["properties"]["loc_name"] or ""
        if loc_name.lower() == name.lower():
            return feature
    return None


def suggest(features, name):
    # Names that look close to what was typed, e.g. "Olsen Hall" → "Olson Hall"
    names = [f["properties"]["loc_name"] for f in features if f["properties"]["loc_name"]]
    return difflib.get_close_matches(name, names, n=3)


def search_buildings(buildings, query, limit=8):
    # Type-ahead search: "well" → Wellman Hall first, Grounds Shed Wellman later
    query = query.strip().lower()
    if not query:
        return []
    matches = []
    for building in buildings:
        name = (building["properties"]["loc_name"] or "").strip()
        if query not in name.lower():          # skips blank names too
            continue
        category = building["properties"]["type1_name"]
        rank = (                               # Python compares these left to right
            CATEGORY_ORDER.index(category) if category in CATEGORY_ORDER else len(CATEGORY_ORDER),
            any(ch.isdigit() for ch in name),              # numbered names last: "Well A7" is a water well
            0 if name.lower().startswith(query) else 1,    # "well" → "Wellman" before "Grounds Shed Wellman"
            name,                                          # then A to Z
        )
        matches.append((rank, building))
    matches.sort(key=lambda item: item[0])
    return [building for rank, building in matches[:limit]]
