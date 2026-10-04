# ParkOS

**Never forget to pay for parking at UC Davis again, and always know the cheapest lot near your class.**

## Video

VIDEO: https://youtu.be/TjIUbDBwllk


---

## Why I built it

I kept getting parking tickets on campus. I'd drive in, rush to class, and forget to pay. I also found
that most students (even ones who've been here for years) don't know which lots are cheapest.

ParkOS fixes both:

1. **Reminders:** you add your class schedule, and ParkOS emails you before your first class each day:
   *"Class at 10:00 in Olson Hall. Don't forget to pay for parking."*
2. **Cheapest parking:** for each class building (or your current location), it shows the cheapest lot
   you're allowed to use, how long the walk is, and how much you save compared with the closest lot.

## How it works (the whole cycle)

```
 1. Sign up            2. Add your schedule          3. ParkOS plans each day         4. You get an email
 email + password  →   upload a calendar file or  →  first class − 30 min = reminder → "Class at 10:00.
                       a Schedule Builder PDF,        + cheapest allowed lot nearby     Cheapest nearby:
                       or fill in a week grid                                          Lot 2, $3.75"
```

- **The reminder always goes out**, even if ParkOS doesn't recognise your class building. A missing
  building only removes the parking suggestion.
- **One reminder per day**, before your first class, because you pay a daily rate once and stay parked.
- **Only lots you can actually use** are suggested. For example, students can't park in A lots until 5 pm.
- **Best / Cheapest / Closest:** pick what matters to you. "Best" is the cheapest lot within a
  10-minute walk.

## Where the data came from

There's no official "UC Davis parking API", so I found and combined public sources:

| Data | Source | How I got it |
|---|---|---|
| **124 parking lot outlines** with their zone (A, C, L…) | UC Davis's official campus map (an ArcGIS map service) | I opened the campus map website, found the map service it loads its data from, and queried it for everything tagged "Transportation & Parking", downloaded as GeoJSON |
| **1,491 building outlines** (Olson Hall, Wellman Hall…) | The same campus map service | Same query, everything that isn't parking |
| **Prices per zone** (2026–27) | [UC Davis Transportation Services rates page](https://transportation.ucdavis.edu/types_and_rates) | Copied by hand into `data/zone_rates.csv` (the site blocks automated requests) |
| **Real walking and driving times** | Google Routes API | Asked once per lot-and-building pair, then cached so each answer is only paid for once |

What I found while cleaning the data:
- 71 lots have no name in the official data, including 7 of the cheapest (L zone), so they're hidden from suggestions
- "Lot 4" appears twice (a duplicate), and "Lot 5" is both a C+ and a C lot, so the app always shows the zone next to the name
- C+ costs the same as A ($6.50), so the real cheap options for students are **L ($3.75)** and **C ($5.50)**
- Example: parking at Lot 2 instead of the lot next to Olson Hall saves **$2.75 a day, about $140 a quarter**

The downloaded files in `data/` are kept exactly as downloaded, and all cleaning happens in code, so
re-downloading always gives the same result.

## Technologies

| Layer | What I used | Why |
|---|---|---|
| **Front end** | React 19, TypeScript, Vite, Leaflet (map) | Leaflet draws the lot outlines straight from GeoJSON, coloured by price |
| **Back end** | Python, Flask, gunicorn | Small and clear: each route reads the request, calls the parking logic, returns JSON |
| **Database** | PostgreSQL | User accounts, schedules, settings and a log of sent reminders |
| **Login** | Email + password, salted scrypt hash, signed session cookie | Passwords are never stored, only a hash that can check them |
| **Email** | Brevo | Sends the reminder emails |
| **Maps / routes** | Google Routes API | Real walking and driving times instead of straight-line guesses |
| **Hosting** | Railway (back end + database), Vercel (front end) | Railway keeps a server running all the time, which the reminder job needs |

### How the pieces talk to each other

```
 Browser (React, on Vercel)
    │  fetch("/api/recommendations?building_id=439")
    ▼
 Vercel forwards every /api/... request to Railway, so the browser sees one website
    ▼
 Flask API (on Railway)  ──►  parking logic in Python (lots + buildings held in memory)
    │                    ──►  Google Routes API (walking/driving times, cached)
    │                    ──►  PostgreSQL (this user's schedule and settings)
    ▼
 JSON back to the browser  →  drawn on the page and the map

 Reminder job (inside the Flask server, every 30 seconds)
    for each user: is it time for today's reminder? → send the email with Brevo → log it so it's never sent twice
```

**A design rule I followed:** the back end decides and the front end only displays. Prices, walk times,
which lots you're allowed to use and when to remind you are all worked out in Python, so every
screen and every email agree.

**Why no PostGIS (the usual "maps in Postgres" add-on)?** There are only 124 lots and about 1,500
buildings. They fit in memory, and Python finds the nearest lots in milliseconds. So the map data stays
as files in the repo, and Postgres only holds what users create.

## Project layout

```
backend/
  app.py              creates the Flask app and starts the reminder job
  api/                one file per group of routes (auth, schedule, settings, reminders, map…)
  parking/            the core logic: prices, permissions, nearest lots, walk times, reminder planning
  schedule_import/    reads .ics calendar files and Schedule Builder PDFs into a list of classes
  notify/             builds and sends the reminder email
  jobs/               the background reminder job
  db/                 database tables (schema.sql) and the queries for each table
frontend/
  src/screens/        onboarding, week, schedule, map and settings pages
  src/api/client.ts   every call to the back end, in one place
data/                 lot and building outlines (GeoJSON) and the price table (CSV)
docs/PRD.md           the product plan and the API contract between front end and back end
```

## Running it locally

You need Python 3.13, Node 22 with pnpm, and a PostgreSQL database.

1. Create `backend/.env` with:
   ```
   DATABASE_URL=postgresql://...      # your Postgres connection URL
   SECRET_KEY=any-long-random-string
   GOOGLE_MAPS_API_KEY=...
   EMAIL_PROVIDER=brevo
   BREVO_API_KEY=...
   BREVO_SENDER_EMAIL=you@example.com
   ```
2. Back end (from the repo root):
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\python backend\app.py          # http://localhost:5000, creates the tables on first run
   ```
3. Front end:
   ```
   cd frontend
   pnpm install
   pnpm dev                                     # http://localhost:8443
   ```

## What's next

- Name the 71 unnamed lots so they can be suggested
- ParkMobile zone numbers for each lot (they're only printed on signs)
- Phone notifications (web push) alongside email
- Street parking (some streets allow L and C permits)

## Early sketch

<img width="634" height="714" alt="Early drafting sketch" src="https://github.com/user-attachments/assets/8e32080f-84d3-49f3-a782-f8531add158b" />
