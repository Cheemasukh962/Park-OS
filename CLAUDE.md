# UC Davis Parking App: project context and conversation summary

This file summarises the planning conversation (Sept 27–28, 2026) between Sukhman and Claude Code, so work can continue on another computer. **Read all of it before doing anything.** Current stage: **planning the data layer. No app code has been written yet.**

---

## 1. About the user and how to work with them
- Sukhman is a UC Davis student building this as a **full-stack portfolio project**.
- **Learning is a main goal.** They want to understand every layer. In a past full-stack project they skipped understanding the JSON part and don't want that again. Explain concepts plainly with examples from this parking project, not abstract ones.
- They like to **plan before building**. Several times they said "just plan, don't build anything yet". Don't write app code until they ask.
- They like **visuals**. They asked for an editable diagram of the database (see section 9).
- They use Windows, VS Code and Claude Code.

---

## 2. The idea
A web app that helps UC Davis students (and staff and visitors):
1. **Remember to pay for parking.** Users enter their class schedule, and the app reminds them before their first class of the day.
2. **Find the cheapest parking.** It shows the cheapest lots the user is allowed to use near their class buildings, or near their current location while the page is open. The user's point: many people, even ones who've been here a while, don't know which lots are cheapest.

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
- `ucd_parking_lots.geojson`: the 124 official lot outlines (main dataset, about 1 MB)
- `taps_pay_stations.geojson`: TAPS layer 2
- `taps_street_parking.geojson`: TAPS layer 4

### Prices: not in any dataset
- The outlines tag each lot with a **zone**, not a price. Every lot in a zone costs the same, so prices go in a small table entered by hand, then joined to lots by zone.
- Source: https://transportation.ucdavis.edu/types_and_rates. **The TAPS website blocks automated requests (403),** so prices must be copied by hand.
- Prices change often: they went up on **Jan 1, 2026** (F +$0.25, A and C+ +$0.40, C/L/M +$0.50) and again on **July 1, 2026**. Store each price with the date it took effect.
- Cheapest to most expensive: **L < C < C+ < A** (price rises closer to the campus core).
- Older reference figures: in 2022 A was $4.60/day and C $3.50/day; visitors were $10/day or $1.50/hour near the Shrem museum. These are out of date.
- Rules:
  - Daily A is for faculty and career staff; students may use A only **after 5pm**.
  - C+ spaces are inside A areas and open to students and employees.
  - UC Davis affiliates get lower ParkMobile rates than visitors, if they sign up with their UCD email.
  - Enforcement is **Mon–Fri, 7am–10pm**. Weekends and holidays only during posted special events.
- F and M zones exist but aren't in the map data.
- Meter prices aren't available. Hourly parking is left out of version 1.

### Other gaps
- **ParkMobile zone numbers per lot are not published.** They'd have to be collected from the signs at each lot.
- **Schedule import:** Sukhman says Schedule Builder can print your schedule with classes and times. Plan: the user pastes the text from the print view and the app parses it. **Still needed:** a real sample (with personal details removed) to see the building-name format, e.g. "WELLMN" vs "Wellman Hall".

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
| Front end | HTML/CSS + JavaScript `fetch` (React maybe later) |
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
- **`lots`**: `id` PK, `source_id` UNIQUE (the campus map's ID, so re-imports don't duplicate), `name`, `zone_code` FK→zones (**nullable** for the 67 Misc. lots), `parkmobile_zone` (nullable, filled in by hand), `geom geometry(MultiPolygon, 4326)`
- **`buildings`**: `id` PK, `caan` UNIQUE (the map's `pk_CAAN`), `name`, `aliases text[]` (schedule short names, e.g. WELLMN), `geom geometry(MultiPolygon, 4326)`
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
  - import script: loads lots and buildings from the campus map service
- **Front end:**
  - onboarding: pick student/staff/visitor → paste schedule → check parsed classes → confirm buildings
  - map: lots coloured by price, class buildings, the recommended lot for each day
  - "cheapest near me" live mode (browser location while the page is open)
  - settings: walk limit, how early to remind, channels

## 11. Suggested build order
1. **Data:** set up Supabase + PostGIS, write `schema.sql`, write the import script, type in the price table
2. **Recommendations:** the query plus a simple map page (useful before schedules exist)
3. **Schedule:** the paste parser plus the building-name aliases
4. **Reminders:** the scheduled job plus email
5. **Extras:** web push, ParkMobile zone numbers, SMS

## 12. Open items and next steps
1. Sukhman reviews and **saves the schema board**. Read it and update the plan.
2. Get a **sample of the Schedule Builder print view** (personal details removed) to design the parser and aliases.
3. Write `schema.sql`.
4. Copy the current zone prices by hand from the rates page (Transportation Services blocks automated requests).
5. Collect ParkMobile zone numbers from lot signs (lower priority).
6. Check whether Schedule Builder can export a calendar file (.ics). Not confirmed.

## 13. Housekeeping
- The session started with a quick check on another repo (`include-davis`, branch `fix/opportunities-page`, commit "fixed opp page"). That isn't part of this project.
- `C:\Users\cheem` (the whole user folder) is a git repo, almost certainly by accident. This `parking` project should get **its own git repo** before pushing to GitHub.
- Sukhman is switching computers and will push this folder to their GitHub repo. The full chat history is not in the repo. It lives at `C:\Users\cheem\.claude\projects\c--Users-cheem-parking\f2a48dd7-69bf-4fba-af6e-e0d19d44210d.jsonl` (it contains personal info, so it should only go into a **private** repo, if at all).
