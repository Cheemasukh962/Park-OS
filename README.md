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
