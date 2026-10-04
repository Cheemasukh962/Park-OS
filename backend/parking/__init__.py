"""Core ParkOS logic, with no web code: can be used by the Flask API, the demo script or tests.

    data.py               campus lots and buildings (loaded once)
    geo.py                points, corners and straight-line distance
    prices.py             who may park in which zone, and for how much
    search.py             finding buildings by name
    ranking.py            ranking lots by walk, and the Best / Cheapest / Closest picks
    trips.py              picking a lot for a drive + walk trip
    google_routes.py      real walking/driving times and route shapes from Google
    arrival.py            when you arrive to park (class start minus 20 min), shared by reminders and the map
    academic_calendar.py  quarter dates and holidays
    reminders.py          planning one day's parking reminder
"""
