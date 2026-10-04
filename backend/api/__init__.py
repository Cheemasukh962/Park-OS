"""The web layer: turns HTTP requests into calls to parking/, and results into JSON.

    errors.py           every error answered as JSON
    params.py           reading and checking query parameters
    shapes.py           shaping results into the JSON the front end expects (docs/PRD.md section 6)
    store.py            saving the schedule and settings (a JSON file until the database)
    schedule_import.py  uploading a schedule file (.ics or .pdf) to turn into classes
    buildings.py ...    one Blueprint (group of routes) per resource
"""
