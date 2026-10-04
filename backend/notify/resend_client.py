"""Sending email through Resend (resend.com): one HTTPS request per email.

Free plan, no domain set up: the sender must be onboarding@resend.dev, and Resend only
delivers to the email address the Resend account was created with.
"""
import json
import urllib.error
import urllib.request

from config import RESEND_API_KEY, RESEND_FROM
from notify.errors import EmailError

RESEND_URL = "https://api.resend.com/emails"


def send_email(to, subject, html, text):
    """Send one email. Returns Resend's id for it; raises EmailError with Resend's reason if it fails."""
    if not RESEND_API_KEY:
        raise EmailError("RESEND_API_KEY is missing from backend/.env")
    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps({"from": RESEND_FROM, "to": [to], "subject": subject, "html": html, "text": text}).encode(),
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json",
                 "User-Agent": "ParkOS/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read())["id"]
    except urllib.error.HTTPError as error:
        # Resend explains what went wrong in the response body, e.g. "You can only send testing emails to ..."
        detail = error.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except ValueError:
            pass
        raise EmailError(f"Resend refused the email ({error.code}): {detail}")
    except (urllib.error.URLError, TimeoutError) as error:
        raise EmailError(f"Couldn't reach Resend: {error}")
