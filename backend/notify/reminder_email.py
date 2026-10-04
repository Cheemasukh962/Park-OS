"""The reminder email: "Pay for parking" plus today's class and the suggested lot.

Built from the same day plan the Week page shows (api/reminders.day_json), so the email and the
app always agree. Every email has an HTML version (what most inboxes show) and a plain-text one.
"""
from html import escape


def clock(hhmm):
    # "16:40" → "4:40 pm"
    hours, minutes = map(int, hhmm.split(":"))
    return f"{hours % 12 or 12}:{minutes:02d} {'pm' if hours >= 12 else 'am'}"


def dollars(cents):
    return f"${cents / 100:.2f}"


def build_reminder_email(day):
    """day: one entry from the reminder plan (with remind_at, first_class, suggestion).
    Returns (subject, html, text)."""
    first = day["first_class"]
    where = f" in {first['building_name']}" if first["building_name"] else ""
    class_line = f"Your first class today is {first['course']} at {clock(first['start'])}{where}."
    subject = "Pay for parking"

    lot = day.get("suggestion")
    if lot:
        walk = f"{'~' if lot['walk_source'] == 'estimate' else ''}{lot['walk_min']} min walk"
        lot_line = f"Suggested lot: {lot['lot_name']} (zone {lot['zone']}), {dollars(lot['price_cents'])}, {walk}."
        extras = []
        if lot["saves_cents"] > 0:
            extras.append(f"Saves {dollars(lot['saves_cents'])} vs {lot['closest']['lot_name']}.")
        if lot["over_walk_limit"]:
            extras.append("It's longer than your walk limit: no closer lot fits all of today's classes.")
        if lot["access_note"]:
            extras.append(lot["access_note"] + ".")
        extra_line = " ".join(extras)
    else:
        lot_line = "Add a building to today's classes in ParkOS to get a parking suggestion."
        extra_line = ""

    text = "\n".join(line for line in [
        "PAY PARKING NOW",
        "",
        class_line,
        lot_line,
        extra_line,
        f"Directions: {lot['directions_url']}" if lot else "",
        "",
        "Pay in the ParkMobile app before you leave your car.",
        "- ParkOS",
    ] if line is not None)

    # Inline styles only: email apps ignore <style> blocks and external CSS
    lot_html = ""
    if lot:
        lot_html = f"""
      <div style="border:1px solid #ffbf00;background:#fff9e6;border-radius:10px;padding:14px 16px;margin:16px 0">
        <div style="font-size:13px;color:#13639e;font-weight:700;text-transform:uppercase;letter-spacing:.05em">Suggested lot</div>
        <div style="font-size:20px;font-weight:800;margin:4px 0">{escape(lot['lot_name'])} · zone {escape(lot['zone'])}
          <span style="float:right">{dollars(lot['price_cents'])}</span></div>
        <div style="color:#13639e">{escape(walk)}</div>
        {f'<div style="margin-top:8px">{escape(extra_line)}</div>' if extra_line else ''}
        <a href="{escape(lot['directions_url'])}" style="display:inline-block;margin-top:10px;color:#022851;font-weight:700">Directions in Google Maps →</a>
      </div>"""
    else:
        lot_html = f'<p style="color:#13639e">{escape(lot_line)}</p>'

    html = f"""<div style="font-family:Arial,Helvetica,sans-serif;color:#022851;max-width:520px;margin:auto;padding:24px">
      <div style="font-weight:800;font-size:14px;letter-spacing:.08em;color:#13639e">PARKOS</div>
      <h1 style="font-size:30px;margin:8px 0 6px">PAY PARKING NOW</h1>
      <p style="font-size:16px;margin:0">{escape(class_line)}</p>
      {lot_html}
      <p style="font-size:14px">Pay in the ParkMobile app before you leave your car.</p>
      <p style="font-size:12px;color:#6683a0;margin-top:24px">You're getting this because reminders are on in ParkOS.
        Turn them off or change the time under Edit reminders.</p>
    </div>"""
    return subject, html, text
