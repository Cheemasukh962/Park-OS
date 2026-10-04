"""Picks the email service from EMAIL_PROVIDER in backend/.env ("brevo" or "resend").

Both senders have the same send_email(to, subject, html, text) shape, so the rest of the app
(the reminder job, the test button) never knows or cares which one is used.
"""
from config import EMAIL_PROVIDER
from notify import brevo_client, resend_client
from notify.errors import EmailError

PROVIDERS = {"brevo": brevo_client.send_email, "resend": resend_client.send_email}


def send_email(to, subject, html, text):
    send = PROVIDERS.get(EMAIL_PROVIDER)
    if send is None:
        raise EmailError(f"EMAIL_PROVIDER must be one of {sorted(PROVIDERS)}, not {EMAIL_PROVIDER!r}")
    return send(to, subject, html, text)


__all__ = ["send_email", "EmailError"]
