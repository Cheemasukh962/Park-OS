"""Sending reminders to people.

    sender.py          picks the email service from EMAIL_PROVIDER in backend/.env
    brevo_client.py    Brevo: sends to anyone from a verified sender address (no domain needed)
    resend_client.py   Resend: test mode only delivers to your own account email until you verify a domain
    errors.py          EmailError, raised by every sender
    reminder_email.py  turns a planned reminder into the email's subject, HTML and plain text
"""
