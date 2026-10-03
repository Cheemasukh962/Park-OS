# UC Davis Parking App: project context and conversation summary

This file summarises the conversations (Sept 27–28 and Oct 1–2, 2026) between Sukhman and Claude Code, so work can continue on another computer. **Read all of it before doing anything.** Current stage: **prototyping the core logic in plain Python** (`backend/howfar.py`, `backend/reminders.py`, see section 14), and a **front-end layout with mock data** in `frontend/` on the `frontend` branch (section 15). No database or Flask yet, and the front end doesn't talk to any back end yet. The front-end brief is `docs/PRD.md`.

---

## 1. About the user and how to work with them
- Sukhman is a UC Davis student building this as a **full-stack portfolio project**.
- **Learning is a main goal.** They want to understand every layer. In a past full-stack project they skipped understanding the JSON part and don't want that again. Explain concepts plainly with examples from this parking project, not abstract ones.
- They like to **plan before building**. Several times they said "just plan, don't build anything yet". Don't write app code until they ask.
- They like **visuals**. They asked for an editable diagram of the database (see section 9).
- They use Windows, VS Code and Claude Code.
- **Before changing code, say which files will change, how and why**, and wait for approval. A tested preview (written in the scratchpad and run, with real output shown) works well. After a change, explain what changed and why, line by line where it helps.
- They **may be interviewed on this project**, so explain where each piece of data came from and why each decision was made, in terms they could repeat.
- **Don't add Claude as a co-author** on their commits.
- Their Python is **3.15.0a5 (an alpha)**. The prototypes only use the standard library, but install Python 3.13 before adding packages like Flask or psycopg.

---

## 2. The idea
A web app that helps UC Davis students (and staff and visitors):
1. **Remember to pay for parking.** Users enter their class schedule, and the app reminds them before their first class of the day.
2. **Find the cheapest parking.** It shows the cheapest lots the user is allowed to use near their class buildings, or near their current location while the page is open. The user's point: many people, even ones who've been here a while, don't know which lots are cheapest.

### The main flow (set by Sukhman, Oct 2): reminders first, suggestions are a bonus
```
1. Schedule in       →  2. Times              →  3. Reminder               →  4. Suggestion (optional)
   manual entry OR       first class each          "Class at 10:00. Don't        only for buildings we know:
   upload & parse        day, minus lead time      forget to pay for parking."   "Cheapest nearby: Lot 2, $3.75"
```
- **The reminder must always go out, even when no building is known.** A missing or unmatched building only removes the suggestion; it never blocks or crashes the reminder.
- **Manual entry comes before the parser.** It doesn't need the Schedule Builder sample, and both produce the same list of classes, so the parser can be added later without changing anything downstream.

---

## 3. How the idea changed

### First version (dropped): GPS geofencing
The first idea was to track the user's location and notify them ("pay for parking") when they enter a parking zone, by text, email or phone notification. Their main worry: **don't notify someone who is just driving past.**

What the research found:
- **Telling "parked" from "driving past"** needs several signals together:
  - they're inside a lot outline, plus about 15 m of margin for GPS error
  - the phone's motion sensors report a switch from driving to walking (Android: Activity Recognition Transition API; iOS: Core Motion's motion-activity updates). This is the strongest signal.
  - they stay in the lot for 1–3 minutes (Android has a built-in "dwell" geofence trigger with a delay you set; iOS needs your own timer)
  - it's enforcement hours and they don't hold a permit for that zone
  - Optional: the phone disconnecting from the car's Bluetooth or CarPlay is a strong "just parked" signal.
- **A website can't do this.** Browsers can't watch location in the background, and no browser supports geofencing.
- **It needs a native app,** e.g. React Native with Expo using a custom build (not Expo's basic mode), plus `expo-location` and `expo-task-manager`, or `transistorsoft/react-native-background-geolocation` (paid for Android release builds).
- Phones cap how many areas an app can watch: 20 on iOS, 100 on Android. The workaround is a few big circles around campus to wake the app, then a point-in-polygon check in the app (turf.js).
- No existing open-source campus parking-reminder app was found. The closest example is `kielni/ucsc-parking` (UC Santa Cruz lots from OpenStreetMap).

### Current version: a web app with schedule-based reminders
Sukhman switched to a **web app** because it's easier. Reminders come from the **user's schedule**, not GPS. The **cheapest-parking finder** was added as a core feature.

---

## 4. Data sources (all public, no API key needed)

### Main source: the official UC Davis campus map service
`https://services6.arcgis.com/KsqDFceSbJQwtqnH/arcgis/rest/services/base_facilities/FeatureServer/0`
- Layer 0 is polygons (1,615 features) with fields: `type1_name`, `type2_name`, `loc_name`, `pk_CAAN`, `lat`, `lng`, `campus`, `status`, `Shape__Area`, and others.
- Query with `where=type1_name='Transportation & Parking'` to get **124 parking lot outlines**. The zone is in `type2_name`:
  - A Permit Parking: 20
  - C (Visitor) Permit Parking: 23
  - C+ Permit Parking: 2
  - L (Visitor) Permit Parking: 12
  - Misc. Parking Lot: 67 (no zone, so price unknown)
- Lot names look like "Lot 47", "Quad Parking Structure", "Gateway Parking Structure", "Pavilion Parking Structure". The name "Lot 4" appears twice.
- The **same layer has building outlines** under other `type1_name` values (Academic & Administration, Housing & Dining, Athletics & Recreation, Support, Other). Building ID: `pk_CAAN`.
- Layer 3 = departments by building; layer 4 = 836 location points.
- Add `outSR=4326&f=geojson` to get standard latitude/longitude GeoJSON.
- Found by reading the data behind the campus map app, ArcGIS item `b53d9d884d004496aa0a44c8a2231516`.

### Transportation Services (TAPS) parking service
`https://utility.arcgis.com/usrsvcs/servers/695b27fda2254b848484b97cbed10b4d/rest/services/Taps_Interactive_Parking/MapServer`
- Layer 0: visitor information (points)
- Layer 1: 25 parking meters (points, no prices)
- Layer 2: 53 "Parking Lots". These are actually **pay-station points** named "VP 1", "VP 50", etc., with type Visitor / Visitor-ACL. They're **points, not outlines**, so they can't be used to check whether someone is inside a lot.
- Layer 3: service vehicle gates
- Layer 4: 22 street parking lines (e.g. "Restricted Access")
- Found through the TAPS interactive parking app, ArcGIS item `9d85223d796646cda1ea090e21329024` → web map `76b7e191ead1493797da1562e04f8f64`.

### OpenStreetMap (backup)
- About 155 parking areas in the campus bounding box (38.525,-121.785 to 38.548,-121.735), but patchy tags: only one has a lot number ("VP 16"), and access and fee tags are inconsistent.
- The main Overpass server (`overpass-api.de`) returned 406 errors. The mirror `overpass.kumi.systems` worked.

### Downloaded copies (in `data/`)
- `ucd_parking_lots.geojson`: the 124 official lot outlines with **all fields** (re-downloaded Oct 1; the first copy lacked `OBJECTID`/`GlobalID`)
- `ucd_buildings.geojson`: **1,491 building outlines** (everything in layer 0 that isn't parking; added Oct 1). 124 + 1,491 = all 1,615 features.
- `taps_pay_stations.geojson`: TAPS layer 2 (not used in version 1)
- `taps_street_parking.geojson`: TAPS layer 4 (not used in version 1)
- `zone_rates.csv`: the hand-entered price table (see Prices below)
- The exact queries used (both against `.../base_facilities/FeatureServer/0/query`, with `outFields=*&outSR=4326&f=geojson`):
  - lots: `where=type1_name='Transportation & Parking'`
  - buildings: `where=type1_name<>'Transportation & Parking'`
- `outSR=4326` asks for WGS84 latitude/longitude (what GPS, Leaflet and PostGIS use) instead of the server's Web Mercator metres.
- **The GeoJSON files are kept exactly as downloaded.** All cleaning happens in the import script, so a re-download always gives the same result.

### What checking the data found
**Lots:**
- `lat`/`lng` are empty for lots, and only 3 lots have a `pk_CAAN`. **Use `GlobalID` as the lot's stable ID** (`OBJECTID` can change if the university republishes).
- `status`: 118 Existing, 3 **Restricted** (Lot 31 West/East/South), 3 **Under Construction** (Rice Lane, 3 pieces).
- **71 lots have no name**: 64 Misc. and **7 L lots** (the cheapest zone). The app can't name these in a reminder until they're named by hand.
- **"Lot 4" appears twice at the exact same distance**, probably a duplicate row. **"Lot 5" exists as both C+ and C** (two areas, one name), so always show the zone next to the name.
- 2 lots are MultiPolygons (Valley Hall, 3 pieces; Garrod Street Parking West, 4 pieces); the rest are Polygons.
- `description` says who may park: A = "Faculty and Staff Parking", C+ = "Faculty, Staff, and Student Parking", C and L = "Visitor, Student, Staff, and Faculty Parking".
- Unnamed Misc. lots are often the closest "lots" to a building (e.g. the 3 nearest to Olson Hall), so they must be hidden from recommendations.

**Buildings:**
- Categories (`type1_name`): Other 733, Academic & Administration 382, Housing & Dining 283, Support 61, Athletics & Recreation 32.
- **"Other" is mostly noise**: 138 blank names, 135 greenhouses, 134 animal/vet/agriculture, 73 sheds and barns, 32 trailers, 28 utilities, ~129 unclear (mostly cargo containers). About 64 halls/labs/field buildings could plausibly host a class.
- Name matching must prefer Academic buildings: "Wellman" also matches "Grounds Shed Wellman" (Other).
- 3 buildings are MultiPolygons (e.g. Goat Sheds, 12 pieces). Wellman Hall's CAAN is 4050.

### Prices (FY 2026–27, effective July 1, 2026), stored in `data/zone_rates.csv`
Copied by hand by Sukhman from https://transportation.ucdavis.edu/types_and_rates (the site blocks automated requests, HTTP 403).

| Zone | Daily price | Who |
|---|---|---|
| A | $6.50 | Employees 7am–5pm; students after 5pm |
| C+ | $6.50 | Employees and students |
| C | $5.50 | Affiliate rate (students and staff) |
| L | $3.75 | Affiliate rate |
| F | $2.75 | Affiliate rate, **but no F lots are in the map data** |
| M | $3.75 | **Motorcycles and mopeds only.** Left out on purpose |
| CH | $21.50 | Chancellor's Office only. Left out |
| Visitor | **$19.00 flat** | Non-affiliates: C, L and F anytime; **A and C+ after 5pm** and weekends during events |
| EV | $4.00 add-on | Left out |
| DSA (disabled) | $0.00 | Left out |

- **C+ costs the same as A**, so it's never a "cheap" option. Cheapest to most expensive for students: **L < C < C+ = A**.
- For visitors every zone costs $19, so only distance matters for them.
- Prices change often: they went up on Jan 1, 2026 and again on July 1, 2026. Keep old rows as history and use `effective_from` (not used by the prototype yet, since there's only one price set).
- Enforcement is **Mon–Fri, 7am–10pm**. Weekends and holidays only during posted special events.
- UC Davis affiliates get lower ParkMobile rates than visitors, if they sign up with their UCD email.
- Meter prices aren't available. Hourly parking is left out of version 1.

### Street parking: version 2
- TAPS layer 4 has 22 street segments: 10 "Restricted Access", 6 "L, C, Visitor Permit", 6 "C, Visitor Permit". So 12 are cheap parking.
- Left for version 2 because: segments allow **several zones** (doesn't fit one `zone_code`), they **hold few cars** (recommending them risks sending everyone to a full street), they have **no names**, they're **lines not areas** (needs its own table or `ST_Buffer`), and the source is maintained separately from the official map.
- "Garrod Street Parking West" (L) is already in the official lots data, so it's in version 1 anyway.

### Other gaps
- **ParkMobile zone numbers per lot are not published.** They'd have to be collected from the signs at each lot.
- **ParkMobile numbers are optional.** Without them the reminder just says "Pay in ParkMobile", and the ParkMobile app can find the zone from the phone's location.
- **Schedule import:** Sukhman says Schedule Builder can print your schedule with classes and times. Plan: the user pastes the text from the print view and the app parses it. **Still needed:** a real sample (with personal details removed) to see the building-name format, e.g. "WELLMN" vs "Wellman Hall".
- **Academic calendar:** the prototype uses **placeholder** Fall 2026 dates (Sep 23 – Dec 11; Veterans Day Nov 11; Thanksgiving Nov 26–27). Check them against the real UC Davis calendar.

---

## 5. Cheapest-parking feature: design notes
- Lots in the same zone all cost the same, so ranking by price alone produces lots of ties. The useful output is the **trade-off**: "Lot X saves you $Y but adds a 6-minute walk."
- **Measure from class buildings, not just GPS.** People choose parking before they leave home. The browser's location can be an extra "near me right now" mode while the page is open.
- Recommend two things per day:
  - the cheapest lot the user is allowed to use within their walk limit (default 10 minutes)
  - the closest lot overall
- **Only show lots the user can use**, based on affiliation (student/staff/visitor) and time of day (e.g. A after 5pm for students).
- **Distance:** straight-line distance to the **nearest edge** of the lot (PostGIS `ST_Distance`), not to its centre, because big structures skew the centre point. Real walking routes (OSRM, OpenRouteService) can come later.
- **One reminder per day:** you pay a daily rate once and stay parked, so remind before the **first class** and pick a lot based on all of that day's buildings (e.g. the cheapest lot that keeps the longest walk under the limit).
- Example reminder: *"Class at 10:00 in Wellman. Cheapest option: Lot 47 (C zone, $X), 7-minute walk. Pay in ParkMobile, zone ####."*
- **Permission is checked at arrival time** (the first class), because you park once. Arriving at 8am means no A lots all day for a student, even with a 6pm class.
- If no allowed lot is within the walk limit, fall back to the closest lot so the user still gets a suggestion.
- **Parking priority (Oct 3):** the user picks **Best** (default: cheapest within the walk limit, which is what the prototype does), **Cheapest** (ignore the walk limit) or **Closest** (shortest walk, any price). The front-end layout already has these as chips.
- **"Use my location" uses the browser Geolocation API**, not Google. It's free with no key; the browser returns latitude/longitude while the page is open, and the back end ranks lots from that point with the same logic as from a building. **Google's Geocoding API is not needed**: it turns typed addresses into coordinates, a different job (Nominatim is the free option if address search is ever wanted). Google's Routes API could later replace straight-line walk estimates with real walking times. Location works only on HTTPS and only while the page is open, and it fits best when already near campus; the schedule-based suggestion stays the default for planning from home.

**First real results** (prototype, student, 10am, 10-minute limit):

| Class building | Cheapest within 10 min | Closest | Saves per day |
|---|---|---|---|
| Olson Hall | Lot 2 (L), $3.75, 10 min | Lot 5 (C+), $6.50, 2 min | $2.75 |
| Kemper Hall | Lot 2 (L), $3.75, 8 min | Lot 47 (C), $5.50, 2 min | $1.75 |
| Shields Library | Lot 2 (L), $3.75, 9 min | Lot 5 (C+), $6.50, 3 min | $2.75 |
| Wellman Hall | Quad Structure (C), $5.50, 4 min | Lot 15 (C+), $6.50, 3 min | $1.00 |
| Giedt Hall | unnamed L lot, $3.75, 9 min | Pavilion Structure (C), $5.50, 3 min | $1.75 |

$2.75/day over ~50 parking days is **about $140 a quarter**. Lot 2 for Olson is borderline (791 m ÷ 80 m/min = 9.9 min), so small distance errors can flip results near the limit.

---

## 6. Tech stack

### Database: PostgreSQL + PostGIS
Sukhman first suggested MySQL and asked how it differs from PostgreSQL and MongoDB.

| | MySQL | PostgreSQL | MongoDB |
|---|---|---|---|
| Type | Relational | Relational | Document store |
| Map/location support | Basic | **PostGIS**, the standard tool | Decent (points, polygons, "near") |
| Fits this data? | Works | **Best fit** | Weaker fit |

- **Chosen: PostgreSQL + PostGIS**, hosted on **Supabase** (or Neon), which has a free tier.
- **Relational vs non-relational, as explained with this data:**
  - *Relational:* each kind of thing gets its own table and tables point to each other by ID. Zone C's price is stored once, and lots just say "I'm zone C". A price change is **one row**. Looking up a lot's price follows the links (a **join**): lot → zone → price.
  - *Document (MongoDB):* each lot document would carry its own copy of the price. Reading one lot is easy, but a price change means updating every copy, and a missed copy means the data contradicts itself.
  - Rule of thumb: relational fits data made of things that point at each other (users → classes → buildings → lots → zones → prices); documents fit self-contained records.
  - Sukhman understood this: parking data is connected, so relational fits.

### Back end: Python + Flask
- Sukhman wants **Flask + JavaScript**. Next.js was the first suggestion, since they already use it in another project (`include-davis` repo, Next.js app router).
- Both count as full stack, because full stack means building all three layers: front end, back end and database.
- **Flask was recommended for learning.** The front end and back end are separate programs that talk only through JSON, so the boundaries are easy to see.

### How data moves through the app, and where JSON fits
Explained step by step, using "cheapest parking near Wellman Hall":
1. The browser runs `fetch("/api/recommendations?building_id=12")` and an HTTP request goes to the server.
2. A Flask route reads `request.args["building_id"]`.
3. Postgres + PostGIS runs a query: `SELECT lots.name, zone_rates.price, ST_Distance(lots.geom, buildings.geom) FROM lots JOIN zone_rates ... JOIN buildings ... ORDER BY price, distance`.
4. Flask turns the rows into Python dicts and then JSON text: `jsonify([{"name": "Lot 47", "price": 3.00, "walk_min": 6}, ...])`.
5. The browser runs `await response.json()`, turning the JSON text back into JavaScript objects, and draws them on the map.

- **JSON** is a plain-text format for passing data between programs. The back end serialises its data to JSON and the front end parses it back.
- JSON appears in three places in this app:
  - API requests and responses
  - **GeoJSON** for map shapes (the `data/*.geojson` files)
  - data the user posts, e.g. saving a class: `{"course": "ECS 36A", "days": "MWF", "start": "10:00", "building_id": 12}`
- **Build the API first and test it with Postman or `curl`** before any front end exists, so the raw JSON is visible.

### The full stack

| Piece | Tool |
|---|---|
| Database | PostgreSQL + PostGIS (Supabase or Neon) |
| Talking to the database from Python | SQLAlchemy, or `psycopg` for raw SQL (GeoAlchemy2 for PostGIS types) |
| Changing the database structure over time | Alembic |
| API | Flask (routes, `request`, `jsonify`) |
| Login | Flask-Login, or Supabase Auth |
| Scheduled reminders | APScheduler (inside Flask) or cron; runs every 5 minutes in `America/Los_Angeles` |
| Email | Resend or SendGrid |
| Front end | **React 19 + TypeScript + Vite + Tailwind v4** (decided Oct 3, when the Figma Make layout arrived), `fetch` for the API |
| User location | Browser Geolocation API (no key) |
| Map | Leaflet (or MapLibre) drawing GeoJSON; lots coloured by price |
| Hosting | Render or Railway for Flask; Supabase for the database |

### Reminder channels (a web app can't wake itself up; the server sends reminders)
1. **Email:** free, works everywhere, easiest. **Start here.**
2. **Web push:** works on Android. On iPhone only if the site is added to the home screen (iOS 16.4+).
3. **SMS (Twilio):** costs money per text and needs carrier (A2P 10DLC) registration first. Maybe later.

Reminders go out Mon–Fri only, skipping holidays, breaks and dates outside the quarter.

---

## 7. What needs to be stored
Sukhman's first list: schedule, reminders, favorites, parking data, recommendations. Claude's additions and corrections:
- **Missing:** users, buildings, academic calendar (terms and closures), a sent-reminders log, push subscriptions.
- **Split parking data into** lots, zones and zone prices, because prices change on their own schedule.
- **Split reminders into** settings (what the user chose) and a sent log (what the system did).
- **Recommendations are calculated when requested, not stored.** Storing them would mean updating them whenever a price, class or lot changes. A table would only make sense later for history, e.g. "how much has this app saved me this quarter."

The data falls into three groups:
- **Campus data:** you load it; it rarely changes
- **User data:** people create it
- **System data:** the app produces it

---

## 8. Database plan (draft, 12 tables)

Terms explained to the user: primary key (PK), foreign key (FK), one-to-many, many-to-many (through a table in between), one-to-one, UNIQUE, NULL.

### Campus data
- **`zones`**: `code` text PK (`'A'`, `'C'`, `'C+'`, `'L'`, used as the key itself), `name`, `description`
- **`zone_rates`**: `id` PK, `zone_code` FK→zones, `affiliation` (student/staff/visitor), `price_cents` integer, `available_from` time (nullable; e.g. A for students from 17:00), `effective_from` date
  - **Money is stored as whole cents** ($3.50 = 350) to avoid rounding errors.
  - No row for a zone and user type means that user can't park there.
  - Old rows are kept as price history.
- **`lots`**: `id` PK, `source_id` UNIQUE (**the map's `GlobalID`**, so re-imports don't duplicate), `name` (nullable: 71 lots have none), `zone_code` FK→zones (**nullable** for the 67 Misc. lots), **`status`** (`open`/`restricted`/`closed`), **`status_reason`** (nullable text, e.g. "Under construction"), `parkmobile_zone` (nullable, filled in by hand), `geom geometry(MultiPolygon, 4326)`
  - Import maps `Existing` → open, `Restricted` → restricted, `Under Construction` → closed with reason "Under construction". Recommendations use `open` lots only. **Flag rather than delete**, so a lot can be reopened by changing one value.
- **`buildings`**: `id` PK, `caan` UNIQUE (the map's `pk_CAAN`), `name`, **`category`** (from `type1_name`; the parser searches Academic first and falls back to the rest), `aliases text[]` (schedule short names, e.g. WELLMN), `geom geometry(MultiPolygon, 4326)`
- **`terms`**: `id` PK, `name` ("Fall 2026"), `start_date`, `end_date`
- **`closures`**: `date` PK, `reason` ("Thanksgiving")

### User data
- **`users`**: `id` PK, `email` UNIQUE, `password_hash` (never the real password; hash with bcrypt or argon2), `affiliation`, `walk_limit_min` (default 10), `created_at timestamptz`
- **`reminder_settings`** (one-to-one): `user_id` is both PK and FK→users (this forces one row per user), `enabled`, `lead_minutes`, `channel` ('email'/'push'). These columns could live on `users` instead; kept separate as one-to-one practice.
- **`schedule_entries`**: `id` PK, `user_id` FK, `term_id` FK, `course` ("ECS 36A"), `section_type` (LEC/DIS/LAB), `days smallint[]` ({1,3,5} = Mon/Wed/Fri, 1 = Monday), `start_time`/`end_time` time (campus local), `building_id` FK→buildings (**nullable**, for when the parser can't match; the user fixes it), `room`
- **`favorites`** (many-to-many, users ↔ lots): `user_id` FK, `lot_id` FK, `created_at`; **combined PK (user_id, lot_id)** so a lot can't be saved twice

### System data
- **`reminders_sent`**: `id` PK, `user_id` FK, `reminder_date`, `lot_id` FK (nullable; the lot recommended at the time), `channel`, `status` (sent/failed), `sent_at timestamptz`, with **UNIQUE (user_id, reminder_date)** so the same reminder can't go out twice even if the job runs twice
- **`push_subscriptions`** (later): `id` PK, `user_id` FK, `endpoint` UNIQUE, `keys jsonb`

### Design choices
- **Class times** use `time` (they repeat every week). **Events that happened** use `timestamptz` (stored in UTC). Convert with `America/Los_Angeles`.
- **Days as an array**, checked against `EXTRACT(ISODOW ...)`.
- **Two links are nullable on purpose** (`lots.zone_code`, `schedule_entries.building_id`) because real data is messy. Keep the row and fix it later.
- The only stored snapshot of a recommendation is `reminders_sent.lot_id`.
- **Every shape is stored as MultiPolygon.** The source mixes Polygon and MultiPolygon, and a PostGIS column accepts one type, so the import wraps single Polygons with `ST_Multi`. This costs nothing noticeable: the work depends on the number of corner points, not the type.
- **Measure in metres, not degrees.** `ST_Distance` on 4326 geometry returns degrees. Cast to geography: `ST_Distance(a.geom::geography, b.geom::geography)` returns metres.
- **Add a GiST spatial index** on each `geom` column so Postgres can skip far-away shapes.
- `zone_rates` answers both "may this user park here?" and "how much?": no row, or a time before `available_from`, means not allowed. Misc. lots have no zone, so no row, so they're excluded automatically.

---

## 9. Editable schema diagram
- **Link:** https://claude.ai/artifact/BSFb63c4XTBW9fJZSXy3eT (private to Sukhman's claude.ai account; opens on any device)
- It shows all 12 tables colour-coded by group, with lines for foreign keys.
- Sukhman can: click a table or column to edit it; drag tables; mark items Keep / Not sure / Cut; add or remove columns and tables; leave notes per table and column and in a "Notes for Claude" box; see a "Your changes" list compared with the original; and **Save changes**. Saving publishes a new version, and the board's data sits in a JSON block with id `schema-state`.
- **Next session: read the saved board first** (Artifact tool, `action: "read"`, with the URL) and update the schema from Sukhman's changes before writing `schema.sql`.
- Save hasn't been tested yet (it needs Sukhman to click it). If it fails, ask for the exact message.

---

## 10. Layers overview (planned)
- **Data:** Supabase Postgres + PostGIS with the tables above.
- **Middle (Flask):**
  - schedule parser: pasted text → course, days, times, building (the hard part is matching building names through `aliases`)
  - recommendation engine: one PostGIS query ranking allowed lots by price, then walking distance
  - reminder job: runs every 5 minutes; checks first class of the day, lead time, term dates, closures, and `reminders_sent` to avoid duplicates
  - senders: email first, push later
  - import script: loads lots and buildings from the campus map service, applying the cleaning rules:
    - skip rows with blank names for buildings (lots keep theirs, flagged as unnamed)
    - map lot `status` to open/restricted/closed with a reason
    - turn `type2_name` into a zone code from a fixed list (A, C+, C, L); anything else becomes NULL
    - wrap Polygons as MultiPolygons
    - remove the duplicate "Lot 4"
    - store `type1_name` as the building `category`
- **Front end:**
  - onboarding: pick student/staff/visitor → enter classes manually (or paste schedule) → check classes → confirm buildings (optional)
  - map: lots coloured by price, class buildings, the recommended lot for each day
  - "cheapest near me" live mode (browser location while the page is open)
  - settings: walk limit, how early to remind, channels

## 11. Build phases (agreed Oct 3: Flask before the database)

**Where things stand (Oct 3):**

| Layer | Done | Not done |
|---|---|---|
| Data | Lots, buildings, prices (`zone_rates.csv`) | Database (Supabase) |
| Logic (Python) | Rank lots from a building, price and permission rules, "Best" pick, reminder planning | Rank from a location, Cheapest/Closest, building search |
| API (Flask) | Nothing | Everything: the missing middle |
| Front end | All screens with mock data (section 15) | Calling the API, real "Use my location", mock fixes, Leaflet map |
| Reminders | Planning logic | Sending email on a schedule |

**How the pieces connect:**
```
React (frontend/, port 8443)                  Flask (backend/, port 5000)             Logic + data
  Map page: "Use my location" ──fetch──►  GET /api/recommendations?lat=..&lng=.. ──► rank lots from a point
  Week page: day cards        ──fetch──►  GET /api/reminders/preview             ──► reminders.py
  Grid step: save a class     ──fetch──►  POST /api/schedule                     ──► stored (file now, database later)
  Buildings step: type-ahead  ──fetch──►  GET /api/buildings?q=well              ──► building search
                              ◄──JSON───
```
In development two servers run at once; Vite's proxy forwards `/api/...` to Flask so the browser sees one site.

**Phase 0: Prototype the logic** ~~done~~ (section 14).

**Phase 1: Finish the logic (Python only, nothing to install)**
- `nearest_lots_to_point(lat, lng, ...)` for geolocation (a point is a shape with one corner, so `distance` mostly works as is)
- `priority`: best / cheapest / closest, matching the front-end chips (definitions in `docs/PRD.md` section 7)
- `search_buildings("well")`: partial names, Academic buildings first ("Wellman Hall" before "Grounds Shed Wellman")

**Phase 2: Flask API, no database yet**
- Install Python 3.13, a virtual environment and Flask
- `backend/app.py` with the endpoints in `docs/PRD.md` section 6. Each route is a thin wrapper: read the request, call the existing function, `jsonify` the result
- Schedule and settings saved to a JSON file for now (about 20 lines of throwaway code)
- Test every endpoint with `curl` before React touches it, so the raw JSON is visible

**Phase 3: Connect the front end, one screen at a time** (on the `frontend` branch)
1. Vite proxy plus `src/api.ts` with a TypeScript type per JSON shape
2. Map page: real ranked lots plus **"Use my location"** (geolocation end to end)
3. Buildings step: type-ahead
4. Grid step: saving classes (fix 0-based days and "am/pm" times here)
5. Week page: real reminder preview
6. Settings

**Phase 4: Database.** Supabase + PostGIS, `schema.sql` (section 8), import script with the cleaning rules (section 10). Swap the JSON file for Postgres and the Python distance loop for a PostGIS query. **The front end doesn't change**, because the API returns the same JSON.

**Phase 5: Real reminders.** Scheduled job every 5 minutes, email via Resend, `reminders_sent` to prevent duplicates.

**Phase 6: Accounts and deployment.** Real login (the layout's login screen accepts anything today), then hosting (Render/Railway + Supabase).

**Later:** Schedule Builder parser (needs the sample), Leaflet map, web push, naming the 71 unnamed lots, ParkMobile zone numbers, street parking, SMS.

**Why Flask before the database:** a working full-stack loop (click in React → Flask → real lot data) arrives within a couple of sessions instead of after all the database setup, and Sukhman learns one new layer at a time (API first, then database). The cost is a little throwaway file-storage code.

## 12. Open items and next steps
1. **Next: Phase 1** (show a tested preview before changing files).
2. Commit `docs/PRD.md` (on the `frontend` branch, still uncommitted as of Oct 3).
3. Fix the front-end mock data: Lot 10 is A (not C), Lot 30 is C (not L); see PRD section 6 for the format mismatches (0-based days, "10:00 am" times, price strings).
4. Get a **sample of the Schedule Builder print view** (personal details removed) to design the parser and aliases.
5. Get the **real Fall 2026 calendar** (first day, last day of finals, holidays) to replace the placeholders.
6. Read the **schema board** before Phase 4, in case Sukhman saved edits there; it doesn't yet include the Oct 1–2 changes (GlobalID, status, category).
7. Collect ParkMobile zone numbers from lot signs (lower priority).
8. Check whether Schedule Builder can export a calendar file (.ics). Not confirmed.
9. Small fixes noted: hide "saves $0.00" for visitors; use `effective_from` once a second price set exists; make `zone_letter` check a fixed list instead of the words "Permit Parking".

## 13. Housekeeping
- The session started with a quick check on another repo (`include-davis`, branch `fix/opportunities-page`, commit "fixed opp page"). That isn't part of this project.
- The project now lives at `C:\Users\Cheem\PARKOS`, is **its own git repo**, and is pushed to https://github.com/Cheemasukh962/Park-OS.
- **Branches:** `main` (back-end prototypes and data) and `frontend` (created Oct 3 from `main`; adds `frontend/`). Front-end work goes on `frontend` and is merged into `main` later.
- Run `git pull` before starting work, especially after editing files on github.com. On Oct 2 a README edit made on GitHub caused a merge that opened `MERGE_MSG` in VS Code and blocked the terminal until the tab was closed. `git pull --no-edit` avoids the editor.
- The full chat history from Sept 27–28 is not in the repo. It was at `C:\Users\cheem\.claude\projects\c--Users-cheem-parking\f2a48dd7-69bf-4fba-af6e-e0d19d44210d.jsonl` on the old computer (it contains personal info, so it should only go into a **private** repo, if at all).

---

## 14. Prototype code (plain Python, standard library only)
Both files read `data/` relative to their own location, so they work on any computer. Run from the repo root.

**`backend/howfar.py`: which lots can I use, and what do they cost?** (`python backend/howfar.py`)
- `load` / `find` / `suggest`: read GeoJSON, find a feature by name ignoring capitals, suggest close names on a typo (`difflib`)
- `distance`: closest pair of corners using the haversine formula, a rough stand-in for PostGIS `ST_Distance`
- `lot_label`, `zone_letter`: name or "(unnamed, ID …)"; "C (Visitor) Permit Parking" → "C", Misc. → "?"
- `load_rates` / `price_for(zone, affiliation, hour)`: reads `zone_rates.csv` into `{(zone, affiliation): (price_cents, from_hour)}`; returns the price or `None` if not allowed. Replaced the earlier hand-written `ALLOWED_ZONES`.
- `nearest_lots` → `(metres, price, lot)` sorted by distance; `cheapest_within(ranked, limit)` picks by `(price, metres)`
- Settings at the bottom: `BUILDING_NAME`, `AFFILIATION`, `CLASS_HOUR`. The test code is under `if __name__ == "__main__":` so other files can import the functions without running it.

**`backend/reminders.py`: when to remind, and what to say** (`python backend/reminders.py`)
- Hand-typed `SCHEDULE` (stand-in for manual entry or the parser; `building` may be `None`), placeholder `TERM_START`/`TERM_END`/`CLOSURES`, `AFFILIATION`, `LEAD_MINUTES = 30`
- `skip_reason(day)`: outside the quarter, weekend or closure
- `classes_on(day)`: that weekday's classes, earliest first
- `best_lot(...)`: cheapest allowed lot where the day's **longest** walk is within the limit; falls back to the shortest walk
- `plan_reminder(day)`: reminder time = first class − lead time; the message always includes the reminder and adds "Cheapest nearby: …" only for known buildings. A missing or misspelled building never blocks the reminder.
- It **plans** reminders and prints them for a range of dates. Nothing is sent yet.

What each piece becomes later: `SCHEDULE` → `schedule_entries`; calendar constants → `terms`/`closures`; settings → `users`/`reminder_settings`; the date loop → a job every 5 minutes that sends email and writes `reminders_sent`; the Python ranking loop → one PostGIS query.

---

## 15. Front end (`frontend/`, on the `frontend` branch)
- Built by Sukhman with Figma Make, kept in a separate repo (https://github.com/Cheemasukh962/BuildPRDDocument), then copied into `frontend/` here as commit "basic layout done" (Oct 3). `parkos-source.zip` from that repo was left out: it's a byte-for-byte copy of the same source (ignoring line endings) and its Git LFS pointer was broken.
- **Stack:** React 19, TypeScript, Vite 8, Tailwind CSS v4, Node 22 + pnpm (`cd frontend`, `pnpm install`, `pnpm dev`, port 8443). `frontend/CLAUDE.md` loads Figma's `AGENTS.md`; its claim that a dev server is "already running" only applies inside Figma Make. `vite.config.ts` reads `.figma/make/site.json`, so that folder must stay.
- **Everything is in `src/App.tsx`** (~1,000 lines), switched by a `screen` state: welcome → login → role → method (manual / upload) → grid (week grid + class editor) → buildings → main app: week (day cards), edit-reminders, schedule, map, settings. Colours: UC Davis navy `#022851`, blue `#13639E`, gold `#FFBF00`.
- **All data is hard-coded mock data**; nothing calls an API. The map is a static drawing, not Leaflet. Login accepts anything.
- The day cards and map already have **Best / Cheapest / Closest** chips and a **"Use my location"** button (not wired up).
- **Mock data differs from the planned API** (details in `docs/PRD.md` section 6): days are 0-based (0 = Monday) instead of ISO 1–7, times are "10:00 am" instead of "10:00", prices are strings instead of cents, and two lots have the wrong zone (Lot 10 is A, Lot 30 is C).
