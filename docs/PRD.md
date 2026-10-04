# ParkOS: Product Requirements (front-end brief)

**Status:** draft, updated Oct 3, 2026. **Owner:** Sukhman (UC Davis student, full-stack portfolio project).
**Front-end code:** `frontend/` on the `frontend` branch (React 19 + TypeScript + Vite + Tailwind v4, first exported from Figma Make; commit "basic layout done"). The layout uses hard-coded mock data; connecting it to the API is Phase 3.
**Source of truth for decisions:** [`CLAUDE.md`](../CLAUDE.md) at the repo root. This document is the front-end view of it. If the two disagree, CLAUDE.md wins; flag the conflict.

---

## 1. Summary

ParkOS is a web app for UC Davis students (and staff and visitors) that:

1. **Reminds you to pay for parking.** You enter your class schedule, and the app emails you before your first class each weekday. This is the main feature.
2. **Suggests the cheapest lot you're allowed to use** near your class buildings. This is a bonus that appears only when we know where your classes are.

The problem: UC Davis enforces paid parking Mon–Fri, 7am–10pm, and people forget to pay. Many people, including ones who've been here for years, also don't know which lots are cheapest. Real example: a student with class in Olson Hall who parks in the closest lot (Lot 5, $6.50) instead of Lot 2 ($3.75, 10-minute walk) pays **$2.75 more a day, about $140 a quarter**.

---

## 2. Users

| User | What they need | Notes |
|---|---|---|
| **Student** (primary) | Daily reminder, cheapest allowed lot | Can't use A zone before 5pm |
| Staff / faculty | Same | Can use every zone |
| Visitor | Closest allowed lot | Pays a flat $19.00 in every zone, so price never changes the answer |

Most use will be **on a phone**, often the evening before or the morning of class. Design mobile-first.

---

## 3. The main flow

```
1. Schedule in      →  2. Times             →  3. Reminder               →  4. Suggestion (optional)
   manual entry          first class each        "Class at 10:00. Don't        only if we know a building:
   (paste/upload later)  day, minus lead time    forget to pay for parking."   "Cheapest nearby: Lot 2, $3.75"
```

**Rules the UI must respect:**
- **Building is optional on every class.** The user can skip it. A class without a building still gets a reminder. Never block saving a class because the building is missing.
- **The reminder never depends on the suggestion.** If nothing is known about buildings, the user still gets "Class at 10:00. Don't forget to pay for parking."
- **One reminder per day**, before the **first** class. You pay a daily rate once and stay parked.
- The suggestion considers **all** of that day's buildings: the cheapest lot where the longest walk of the day stays under the user's walk limit (default 10 minutes).

---

## 4. Features and priority

### Version 1 (build these)
| # | Feature | What the user does |
|---|---|---|
| F1 | **Choose affiliation** | Pick student / staff / visitor. Changes which lots and prices apply |
| F2 | **Manual schedule entry** | Add a class: course name, days, start time, optional end time, optional building |
| F3 | **Schedule list** | See, edit and delete classes |
| F4 | **Reminder settings** | Lead time (default 30 min), walk limit (default 10 min), on/off, email |
| F5 | **Reminder preview** | "This week": what reminder goes out each day and when, including skipped days (weekend, holiday) and why |
| F6 | **Parking suggestion per day** | For days with known buildings: cheapest lot within the walk limit, and the closest lot, with the savings |
| F7 | **Building search** | Type-ahead when picking a building ("well" → Wellman Hall) |
| F10 | **"Near me" mode** | Tap "Use my location"; the browser gives latitude/longitude while the page is open, and the app ranks allowed lots from that point (section 6a) |
| F12 | **Parking priority** | Choose **Best / Cheapest / Closest** per day or on the map (definitions in section 7). Default: Best |

### Version 1.1
| # | Feature | Notes |
|---|---|---|
| F8 | **Map** | Real Leaflet map of lots coloured by price, class buildings, and the suggested lot for the day (the current map page is a static drawing) |
| F9 | **Lot finder** | Pick any building and time to see ranked lots (no schedule needed) |
| F11 | **Accounts** | Sign up and log in with email. The layout already has a login screen that accepts anything; whether real accounts are in version 1 is still open (section 10) |

### Later (don't build, but don't design them out)
- **Paste schedule from Schedule Builder** (parser not designed yet; waiting on a sample)
- Web push notifications (Android; iPhone only if the site is added to the home screen, iOS 16.4+)
- Favourite lots
- ParkMobile zone number per lot ("Pay in ParkMobile, zone 4021")
- Street parking, SMS reminders, "money saved this quarter"

### Out of scope
- GPS tracking or geofencing (a website can't run in the background)
- Hourly or meter parking
- Motorcycle (M zone) parking

---

## 5. Screens (as built in `frontend/src/App.tsx`)

All screens are in one file, switched by a `screen` state value. Onboarding first, then the main app with navigation.

| Screen (`screen` value) | Component | Purpose | Features |
|---|---|---|---|
| `welcome` | `Welcome` | What the app does, "get started" | |
| `login` | `Login` | Email + password (preview: anything continues) | F11 |
| `role` | `RoleStep` | Student / staff / visitor | F1 |
| `method` | `MethodStep` | Enter classes manually or upload | F2 |
| `upload` | `UploadStep` | Pick a schedule file (parser doesn't exist yet) | later |
| `grid` | `GridStep` + `WeekGrid` + `ClassPanel` | Week grid; tap a class to edit course and building | F2, F3 |
| `buildings` | `BuildingsStep` | Confirm or skip buildings | F7 |
| `week` | `WeekPage` + `DayCard` | **Home:** one card per weekday with reminder time, first class, Best/Cheapest/Closest chips and the lot; skipped days show the reason | F5, F6, F12 |
| `edit-reminders` | `ReminderSettingsPage` | Reminder timing and email | F4 |
| `schedule` | `SchedulePage` | View and edit classes | F3 |
| `map` | `MapPage` | Ranked lots, filters, **"Use my location"** button, static drawn map | F8, F10, F12 |
| `settings` | `SettingsPage` | Settings | F4 |

**Requirements these screens must keep:**
- The building field must allow **skip / I don't know** (`DES 001` in the mock has no building, which is correct). A class without a building shows a gentle "add building for parking tips" prompt, never an error.
- Day toggles cover **Mon–Fri**; start time required, end time optional.
- Skipped days stay visible, greyed out, with the reason ("Veterans Day", "Weekend").

---

## 6. Data and API contract (draft)

**The API exists (Phase 2, Oct 3):** `backend/app.py`, Flask on port 5000. Run it from the repo root with `.venv\Scripts\python backend\app.py`, then open e.g. http://localhost:5000/api/buildings?q=olson. The shapes below are what it actually returns. If the front end needs a different shape, write it down and tell Sukhman.

- **Storage is temporary:** schedule and settings are saved to `backend/store.json` (one user, git-ignored) until the database in Phase 4. The JSON shapes won't change when that happens.
- **IDs are the map data's `OBJECTID` for now** (Olson Hall = 439, Wellman Hall = 627, Lot 2 = 2209). Always get IDs from the API, never hard-code them; they change when the database arrives.
- **Errors** are always JSON: `{"error": "hour must be 0-23"}`, with status 400 (bad input) or 404 (not found). Show the message to the user or log it.
- Success codes: 200 OK, 201 Created (POST), 204 No Content (DELETE, empty body).
- **The back end decides, the front end displays.** Every rule (who may park where, prices, arrival time, savings, walk-limit checks, class validation, reminder times) lives in Flask. The UI must not re-implement any of them: two copies of a rule drift apart (that's how the Map page once used a different arrival time than the reminders). If a screen needs a new fact, add a field to the API.

### Conventions
- **Money is in whole cents:** `375` = $3.75. Format for display only (`(cents / 100).toFixed(2)`).
- **Days are ISO numbers:** 1 = Monday … 7 = Sunday. A class on Mon/Wed/Fri is `[1, 3, 5]`.
- **Times are campus local time** (`America/Los_Angeles`), 24-hour strings: `"10:00"`, `"14:10"`.
- **Dates** are `"YYYY-MM-DD"`. Timestamps are ISO 8601.
- **GeoJSON coordinates are `[longitude, latitude]`**, longitude first. Leaflet's `L.latLng` takes latitude first, but `L.geoJSON` handles GeoJSON's order for you.
- `building_id` may be `null`.

### Endpoints

**`GET /api/buildings?q=well`** (F7: type-ahead)
```json
[
  { "id": 627, "caan": "4050", "name": "Wellman Hall", "category": "Academic & Administration" }
]
```
Up to 8 results: Academic buildings first, numbered names (water wells like "Well A7") last, names starting with the query before names containing it. A blank query returns `[]`. Abbreviations like "ARC" don't work yet (planned `aliases`, Phase 4).

**`GET /api/schedule`**, **`POST /api/schedule`**, **`PUT /api/schedule/:id`**, **`DELETE /api/schedule/:id`** (F2, F3)
```json
{ "id": 7, "course": "ECS 36A", "days": [1, 3, 5], "start": "10:00", "end": "10:50",
  "building_id": 439, "building_name": "Olson Hall" }
```
POST/PUT send the same object without `id` and `building_name`. `end` and `building_id` may be `null`. Times are 24-hour; `"9:00"` is accepted and tidied to `"09:00"`, `end` must be after `start`. The API **rejects** 0-based days (`[0, 2, 4]`) and 12-hour times (`"10:00 am"`) with a 400.

**`PUT /api/schedule`** replaces the **whole** schedule with a JSON list in one request (onboarding's final save). All classes are checked first: one invalid class means nothing is saved.

**`POST /api/schedule/validate`** checks one class **without saving** and returns it tidied, or a 400 with the reason. The class editor uses this instead of its own rules.

**`POST /api/schedule/import`** (upload step): send the user's schedule file as a multipart upload in a field called `file`. Accepts Schedule Builder's **calendar export (.ics)** or its **printed page (.pdf)**, up to 5 MB. **Nothing is saved**: show the result for review (the Grid step), then save the ticked classes one by one with `POST /api/schedule`.
```ts
const form = new FormData();
form.append("file", fileInput.files[0]);
const result = await fetch("/api/schedule/import", { method: "POST", body: form }).then(r => r.json());
```
```json
{ "source": "pdf",
  "classes": [
    { "course": "EEC 170 Lecture", "days": [1, 3], "start": "10:00", "end": "11:20", "building_id": 205,
      "building_name": "Young Hall", "room": "198", "location": "Young Hall 198", "building_match": "exact name",
      "online": false, "registered": true, "include": true },
    { "course": "EEC 174AY World Wide Web Virtual Lecture", "days": [2, 4], "start": "13:10", "end": "14:00",
      "building_id": null, "building_name": null, "online": true, "registered": true, "include": false }
  ],
  "skipped": [ { "text": "ECS 179 001 Gameplay Programming Final Exam", "reason": "one-time event (e.g. a final exam)" } ] }
```
- `include` is the suggested tick: false for **online** classes (no parking needed) and for classes the PDF says are **not registered**. Let the user change it.
- `building_id` is `null` when the location couldn't be matched: show the building picker for that class. `building_match` says how it was matched.
- To save, send only `course`, `days`, `start`, `end`, `building_id` to `POST /api/schedule`; the other fields are for the review screen.
- Errors (400): not an .ics or PDF, no file, too large, or no classes found.

**`GET /api/settings`**, **`PUT /api/settings`** (F1, F4)
```json
{ "affiliation": "student", "lead_minutes": 30, "walk_limit_min": 10, "priority": "best",
  "reminders_enabled": true, "channel": "email", "email": "student@ucdavis.edu" }
```
PUT sends only the keys being changed, e.g. `{"lead_minutes": 45}`. Limits: `lead_minutes` 0–180, `walk_limit_min` 1–30, `priority` best/cheapest/closest, `channel` email only for now.

**`GET /api/reminders/preview?from=2026-11-02&to=2026-11-08`** (F5, F6): `{"days": [...], "summary": {...}}`, one day entry per date. Optional `&lead_minutes=45` previews a different reminder time without saving (the settings page uses it).
```json
{ "summary": { "next_reminder": { "date": "2026-11-02", "remind_at": "09:30" }, "saves_cents_total": 200 },
  "days": [
  { "date": "2026-11-02", "remind_at": "09:30", "first_class": { "course": "ECS 36A", "start": "10:00", "building_name": "Olson Hall" },
    "message": "Class at 10:00 in Olson Hall. Don't forget to pay for parking. Cheapest nearby: Lot 5 (C zone, $5.50), longest walk today 4 min.",
    "suggestion": { "lot_id": 2223, "lot_name": "Lot 5", "zone": "C", "price_cents": 550, "metres": 278, "walk_min": 4,
                    "walk_source": "google", "directions_url": "https://www.google.com/maps/dir/?api=1&destination=...",
                    "closest": { /* same shape */ },
                    "saves_cents": 0 } },
  { "date": "2026-11-03", "remind_at": "11:40", "first_class": { "course": "MAT 21C", "start": "12:10", "building_name": null },
    "message": "Class at 12:10. Don't forget to pay for parking.", "suggestion": null },
  { "date": "2026-11-07", "skipped": "weekend" }
] }
```
Each pick in `suggestion.picks` (`best` / `cheapest` / `closest`) also has the verdict fields below (`saves_cents`, `over_walk_limit`, `access_note`).
`suggestion` is `null` when no building is known for that day; it uses the user's saved `priority`. Its `walk_min` and `metres` are the day's **longest** walk (to the furthest class building). `saves_cents` is 0 when the pick is also the closest lot: hide the savings line then. `skipped` is one of `"weekend"`, `"outside the quarter"`, `"no classes"`, or a holiday name. `from` defaults to today and `to` to six days later; at most 31 days per request.

**`GET /api/recommendations`** (F9, F10, F12): lots for a trip. Send a class building, the user's location, or **both**:

| Send | Meaning | Ranked by |
|---|---|---|
| `building_id=439` | "I have class in Olson Hall" | walk from lot to class |
| `lat=…&lng=…` | "Use my location", no class picked | drive from you to the lot |
| `building_id=439&lat=…&lng=…` | "Use my location" + class building | **total trip** = drive + walk |

Optional: `hour` (0–23, default: now), `affiliation` and `walk_limit_min` (default: saved settings). **All three picks come back in one response**, so the Best / Cheapest / Closest chips switch instantly without another request:
```json
{ "building": "Olson Hall", "from_location": true, "affiliation": "student", "hour": 10, "walk_limit_min": 10,
  "best":     { "lot_id": 2223, "lot_name": "Lot 5", "zone": "C", "price_cents": 550,
                "drive_min": 4, "drive_metres": 1154, "walk_min": 4, "metres": 278, "walk_source": "google",
                "total_min": 8, "directions_url": "https://www.google.com/maps/dir/?api=1&destination=38.538741,-121.745178&travelmode=driving" },
  "cheapest": { "lot_id": 2209, "lot_name": "Lot 2", "zone": "L", "price_cents": 375, "drive_min": 7, "walk_min": 14, "total_min": 21, ... },
  "closest":  { /* shortest total trip */ },
  "ranked": [ /* up to 10 lots, shortest total trip first, same shape */ ] }
```
(Example: from downtown Davis, `lat=38.5440&lng=-121.7405`, to class in Olson Hall.)

**Every lot object has:**
- `walk_min`, `metres`, `walk_source`: the walk from the lot to class. `null` when no building was sent. `walk_source` is `"google"` for a real walking route or `"estimate"` for our straight-line guess (show "~" before estimates only).
- `drive_min`, `drive_metres`: the drive from the user's location. `null` when no location was sent.
- `total_min`: drive + walk (whichever legs exist).
- `directions_url`: opens Google Maps with **driving directions to the lot**. Use it for a "Directions" button (`<a href={lot.directions_url} target="_blank" rel="noopener">`). No key needed; on phones it opens the Maps app.
- **Verdicts (decided by the API, just display them):** `saves_cents` (vs the closest lot; negative = costs more), `over_walk_limit` (true/false), `access_note` (e.g. `"A: students after 5 pm"`, from the rate table, or null).

**The response also has:**
- `arrival`: which hour the lots are for and why. Without `?hour=`, the API uses the user's **next class at that building, arriving 20 min early** (the same rule as the reminders), e.g. `{"hour": 11, "reason": "next class", "course": "FRS 003 Seminar", "date": "2026-10-08", "start": "12:10"}`; with no building, `"reason": "now"`.
- `allowed_lot_ids`: every lot this user may park in at that hour (draw these solid on the map, others faded).
- `far_from_campus`: true when the user's location is over 30 km from campus.

**How the picks work** (tunable in `backend/parking/trips.py`):
- **Closest**: shortest total trip.
- **Cheapest**: lowest price, ties go to the shortest total trip.
- **Best** with a class building: the cheapest lot whose **walk** is within the walk limit (ties: shortest total trip). With location only: the cheapest lot whose drive is within `DRIVE_SLACK_MIN` (5) minutes of the fastest drive.
- **Real times decide the picks.** Real walks were 1.3–2.3× the straight line: from Olson Hall, Lot 2 looks ~10 min away in a straight line but is 14 min on foot, so Best is Lot 5 (C, $5.50, 4 min).

**`GET /api/route?lot_id=2223&lat=38.5440&lng=-121.7405&building_id=439`** (F8, F10): the trip's shape for drawing on the map. Send the `lot_id` the user picked, plus the same `lat`/`lng` and/or `building_id`:
```json
{ "lot":   { "lot_id": 2223, "lot_name": "Lot 5", "zone": "C", "centre": [38.5387, -121.7452], "directions_url": "…" },
  "drive": { "minutes": 4, "metres": 1154, "path": [[38.5440, -121.7405], [38.5441, -121.7412], …] },
  "walk":  { "minutes": 4, "metres": 278,  "path": [[38.5393, -121.7455], …] } }
```
`path` is a list of `[lat, lng]` points: draw `drive.path` as a solid line and `walk.path` as a dashed one (Leaflet: `L.polyline(path)`). A leg is `null` if it doesn't apply or Google couldn't answer. Answers are cached on the server, so re-selecting a lot is free.

**`GET /api/lots`** (F8): GeoJSON `FeatureCollection` of lot outlines, each with `properties: { id, name, zone, status }`.

### Real data you can mock from now
These files are in `data/` and are what the back end will load:
- `ucd_parking_lots.geojson`: 124 lot outlines. Useful fields: `loc_name`, `type2_name` (zone), `status`, `GlobalID`.
- `ucd_buildings.geojson`: 1,491 building outlines. Useful fields: `loc_name`, `pk_CAAN`, `type1_name` (category).
- `zone_rates.csv`: prices and permissions.

To see what the logic produces without the server, run `python backend/reminders.py` and `python backend/howfar.py` from the repo root.

### Where the current layout differs from this contract
The Figma layout's mock data uses display-friendly formats. Either change the mocks to the API format, or convert in one place (a small `api.ts` module) so the rest of the UI never deals with two formats.

| In `App.tsx` mocks | API format | Note |
|---|---|---|
| `days: [0, 2, 4]` (0 = Monday) | `[1, 3, 5]` (ISO, 1 = Monday) | Off by one: easy to get wrong silently |
| `start: "10:00 am"` | `"10:00"` (24-hour) | `"2:10 pm"` → `"14:10"` |
| `price: "$3.75"` (string) | `price_cents: 375` | Format with `(cents / 100).toFixed(2)` for display only |
| `building: ""` for unknown | `building_id: null` | |
| `top`, `height` on each class | not in the API | Grid layout values; compute them from start/end times in the UI |
| **Lot 10 shown as C, $5.50** | Lot 10 is an **A** lot | Wrong in the mock. A student at 10am can't park there |
| **Lot 30 shown as L, $3.75** | Lot 30 is a **C** lot ($5.50) | Wrong in the mock |
| Lot 2 "720 m" | about 791 m from Olson Hall | Minor |

## 6a. "Use my location" (F10): browser Geolocation API

- Use the **browser's built-in Geolocation API**. It's free and needs **no API key or Google account**. We already have every lot's outline and price, so the back end ranks lots from the point itself.
- Google's **Geocoding** API is a different thing (it turns typed addresses into coordinates) and isn't needed. If address search is ever wanted, OpenStreetMap's Nominatim is a free option.
```ts
navigator.geolocation.getCurrentPosition(
  (pos) => loadRecommendations({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
  (err) => showBuildingPicker(err.message),   // denied, unavailable or timed out
  { enableHighAccuracy: true, timeout: 10000 }
);
```
- **Only ask when the user taps "Use my location"**, never on page load. Browsers show the permission prompt themselves.
- **Always have a fallback:** if the user says no or location fails, let them pick a building instead. Never leave a blank screen.
- Works only on **HTTPS** (`localhost` is fine for development) and **only while the page is open**. No background tracking.
- Location is a good fit **when already on or near campus**. Before leaving home, the schedule-based suggestion (by building) is the right tool, so keep that as the default.
- Accuracy varies (`pos.coords.accuracy`, in metres). If it's worse than ~100 m, show "approximate location".

---

## 7. Domain rules the UI needs to know

### Zones and prices (FY 2026–27, from July 1, 2026)
| Zone | Student | Staff | Visitor | Colour idea for the map |
|---|---|---|---|---|
| L | $3.75 | $3.75 | $19.00 | cheapest |
| C | $5.50 | $5.50 | $19.00 | |
| C+ | $6.50 | $6.50 | $19.00 after 5pm | |
| A | $6.50 **after 5pm only** | $6.50 | $19.00 after 5pm | most expensive |
| Misc. | not shown | not shown | not shown | grey / hidden |

- **Only show lots the user is allowed to use** at their arrival time. Permission is checked at the **first class** time, because you park once.
- **Visitors pay the same everywhere.** Don't show "saves $0.00"; show the closest lot instead.
- **Always show the zone next to a lot name.** "Lot 5" exists as both a C and a C+ area, and "Lot 4" appears twice.
- **71 lots have no name in the data**, including some cheap L lots. Show them as "Unnamed lot (L)" and, on the map, by location.
- Enforcement: Mon–Fri, 7am–10pm. No reminders on weekends, holidays, or outside the quarter.
- Walk times come from Google's walking routes when `walk_source` is `"google"`; otherwise they're a straight-line estimate at 80 m per minute, which **underestimates** real walks. Label estimates as approximate ("~10 min walk").

### Parking priority: Best / Cheapest / Closest (F12)
| Chip | Rule | Olson Hall example (student, 10am) |
|---|---|---|
| **Best** (default) | Cheapest allowed lot **within the walk limit**; ties go to the shorter walk. If nothing is within the limit, the closest lot | Lot 5 (C), $5.50, 4 min (Lot 2 is 14 min on foot) |
| **Cheapest** | Cheapest allowed lot **ignoring the walk limit**; ties go to the shorter walk. Mark it when it's over the limit (the layout's `over-limit` style does this) | Lot 2 (L), $3.75, 14 min: over the limit, so mark it |
| **Closest** | Shortest walk among allowed lots, whatever the price | Lot 5 (C), $5.50, 4 min (by real walk the C part of Lot 5 is closer than the C+ part) |

"Best" is the default for reminders. All three use real walking times when available. For visitors all three give the same price, so only distance matters.

### Copy and tone
- The reminder is the point; keep it short and calm: "Class at 10:00. Don't forget to pay for parking."
- The suggestion is a tip, not an order: "Cheapest nearby: Lot 2 (L, $3.75), ~10 min walk. Saves $2.75 vs Lot 5."

---

## 8. Technical direction

| Piece | Choice |
|---|---|
| Front end | **React 19 + TypeScript + Vite 8 + Tailwind CSS v4**, in `frontend/`. Run with Node 22 and pnpm: `cd frontend`, `pnpm install`, `pnpm dev` (port 8443). Ignore the note in `frontend/AGENTS.md` that the dev server is "already running"; that's only true inside Figma Make |
| Talking to the back end | `fetch`, kept in one module (e.g. `src/api.ts`) with a TypeScript type per JSON shape in section 6 |
| Location | Browser Geolocation API (no key), section 6a |
| Map | Leaflet (or MapLibre), drawing GeoJSON (the current map page is a static drawing) |
| Back end | Python 3.14 + Flask 3.1, JSON API in `backend/app.py` (built Oct 3; port 5000). Setup: `py -3.14 -m venv .venv`, then `.venv\Scripts\python -m pip install -r backend/requirements.txt` |
| Database | PostgreSQL + PostGIS on Supabase (Phase 4; a JSON file until then) |
| Reminders | Email first (Resend or SendGrid), sent by the server on a schedule |
| Hosting | Render or Railway (Flask), Supabase (database) |

- Front end and back end are separate programs that talk **only through JSON**. Keep that boundary visible.
- Mobile-first, accessible (labels on every input, keyboard-usable day toggles, sufficient contrast; don't rely on colour alone for price).

---

## 9. Working with Sukhman
- **Learning is a main goal.** Explain what you build and why, plainly, with examples from this project, especially how data moves (`fetch` → JSON text → JavaScript objects → React state → what renders).
- **Plan before building.** Say which files will change, how and why, and wait for approval.
- They may be **interviewed on this project**, so decisions should be explainable.
- Don't add Claude as a co-author on commits.

---

## 10. Open questions
1. Exact Fall 2026 dates and holidays (back end uses placeholders: Sep 23 – Dec 11, Nov 11, Nov 26–27).
2. Schedule Builder paste format (needed before the import feature).
3. Accounts in version 1, or a single-user local version first? (The layout has a login screen; it accepts anything for now.)
4. ~~Framework~~: decided, React + TypeScript (Oct 3).
5. `App.tsx` is about 1,000 lines in one file. Split it into one file per screen before it grows further?
