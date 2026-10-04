"""POST /api/schedule/import: upload a schedule file and get back classes to review.

Nothing is saved: the front end shows the classes (Grid step), the user fixes or unticks any,
then saves the ticked ones with POST /api/schedule.

    curl -F "file=@schedule_export.ics" http://localhost:5000/api/schedule/import
"""
from flask import Blueprint, jsonify, request

from api.errors import BadRequest
from schedule_import.parse import UnsupportedFile, import_schedule

bp = Blueprint("schedule_import", __name__)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024        # schedules are small; refuse anything over 5 MB


@bp.post("/api/schedule/import")
def import_file():
    upload = request.files.get("file")    # the form field named "file" in a multipart upload
    if upload is None:
        raise BadRequest('send the schedule as a file upload in a field called "file"')
    data = upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise BadRequest("file is too large (5 MB max)")
    try:
        result = import_schedule(upload.filename, data)
    except UnsupportedFile as error:
        raise BadRequest(str(error))
    if not result["classes"]:
        raise BadRequest("couldn't find any classes in this file")
    return jsonify(result)
