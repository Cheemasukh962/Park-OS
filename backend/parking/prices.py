"""Parking prices and permissions, from data/zone_rates.csv (a preview of the zone_rates table).

One table answers two questions: may this user park in this zone at this hour, and for how much?
No row (or an hour before available_from) means not allowed. Money is in whole cents.
"""
import csv

from parking.data import DATA


def load_rates():
    # {("C", "student"): (550, 0), ("A", "student"): (650, 17), ...}
    rates = {}
    with open(DATA / "zone_rates.csv") as f:
        for row in csv.DictReader(f):                      # each row becomes a dict keyed by the header
            from_hour = int(row["available_from"][:2]) if row["available_from"] else 0   # "17:00" → 17
            rates[(row["zone_code"], row["affiliation"])] = (int(row["price_cents"]), from_hour)
    return rates


RATES = load_rates()
AFFILIATIONS = sorted({affiliation for zone, affiliation in RATES})        # staff, student, visitor


def price_for(zone, affiliation, hour):
    # The price in cents, or None if this user can't park in this zone at this hour.
    # Misc. lots ("?") have no row, so they're ruled out automatically.
    rate = RATES.get((zone, affiliation))
    if rate is None:
        return None
    price_cents, from_hour = rate
    return price_cents if hour >= from_hour else None


def dollars(cents):
    return f"${cents / 100:.2f}"                           # 375 → "$3.75"
