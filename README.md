# Park-OS
I get too many parking tickets this needs to stop
basic idea
① Browser (JavaScript)
   fetch("/api/recommendations?building_id=12")
        │  HTTP request goes over the network
        ▼
② Flask route (Python)
   @app.get("/api/recommendations")
   def recommendations():
       building_id = request.args["building_id"]     # read the input
        │
        ▼
③ Database (PostgreSQL + PostGIS)
   SELECT lots.name, zone_rates.price, ST_Distance(lots.geom, buildings.geom)
   FROM lots JOIN zone_rates ... JOIN buildings ...
   ORDER BY price, distance
        │  rows come back
        ▼
④ Flask turns the rows into Python dictionaries, then into JSON text
   return jsonify([{"name": "Lot 47", "price": 3.00, "walk_min": 6}, ...])
        │  HTTP response goes back; the body is JSON text
        ▼
⑤ Browser (JavaScript)
   const lots = await response.json()    # JSON text becomes JavaScript objects
   show the lots on the map


   Drafting 
<img width="634" height="714" alt="image" src="https://github.com/user-attachments/assets/8e32080f-84d3-49f3-a782-f8531add158b" />
<img width="672" height="624" alt="image" src="https://github.com/user-attachments/assets/d5d02f23-8183-42f1-9550-bc04ddab2072" />
Going to break down sql/data most likely 
Users
Schedule
Buildings
Parking lots
Zones and prices
Academic calendar
Favorites
Reminder settings
Sent reminders log
https://claude.ai/artifact/BSFb63c4XTBW9fJZSXy3eT 


Current Problems: 
Basically two main things some places in data are wocky not good/ or side street parking lots which may be a problem

we were going to use polyogn using multip polyogns now

STREET PARKING MAY SKIP YES UJSALLAY CHEAPTER 
DOWNSIDES NOT A LOT OF SPOTS MULTIPLE ZONES IN EACH LANE
GOOD THINK ABOUT ZONES ITS A PARKING RATE IS SAME? 
Lots have no lat/lng, and only 3 have a pk_CAAN. I had assumed lots used the same ID as buildings. They don't, so lots.source_id should store GlobalID. That's a small change to the schema plan.
6 lots are Restricted or Under Construction. The import should filter them out or flag them.
2 lots and 3 buildings are MultiPolygons (one place made of several separate shapes), and the rest are plain Polygons. That's why the schema uses MultiPolygon for every row: the import converts single Polygons so the column holds one consistent type.
733 "Other" entries are sheds, small structures and similar. When we match class buildings we should search Academic buildings first, or "Wellman" will also match "Grounds Shed Wellman".
