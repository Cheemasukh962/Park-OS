"""Sending email through Brevo (brevo.com): one HTTPS request per email.

Unlike Resend's test mode, Brevo can send to anyone without a domain: the "from" address just has
to be a sender you verified in Brevo (Senders & IPs). Caveat: sending AS a @gmail.com address
through another company can fail Gmail's own checks (DMARC), so some mail may land in spam.
A domain of your own fixes that.
"""
import json
import urllib.error
import urllib.request

from config import BREVO_API_KEY, BREVO_SENDER_EMAIL, EMAIL_FROM_NAME
from notify.errors import EmailError

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def send_email(to, subject, html, text):
    """Send one email. Returns Brevo's message id; raises EmailError with Brevo's reason if it fails."""
    if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
        raise EmailError("BREVO_API_KEY and BREVO_SENDER_EMAIL must be set in backend/.env")
    body = {
        "sender": {"name": EMAIL_FROM_NAME, "email": BREVO_SENDER_EMAIL},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
        "textContent": text,
    }
    request = urllib.request.Request(
        BREVO_URL,
        data=json.dumps(body).encode(),
        headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json", "accept": "application/json",
                 # Brevo's firewall blocks Python's default "Python-urllib" label, so name the app
                 "User-Agent": "ParkOS/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read())["messageId"]
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except ValueError:
            pass
        raise EmailError(f"Brevo refused the email ({error.code}): {detail}")
    except (urllib.error.URLError, TimeoutError) as error:
        raise EmailError(f"Couldn't reach Brevo: {error}")
