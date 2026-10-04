"""Secrets and switches from backend/.env (git-ignored), loaded once for the whole back end."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")      # puts .env's lines into os.environ

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
# Postgres connection (Railway: ${{Postgres.DATABASE_URL}}; locally: the database's public URL)
DATABASE_URL = os.environ.get("DATABASE_URL")
# Signs the login cookie so it can't be forged. Must stay the same across restarts, or everyone is signed out
SECRET_KEY = os.environ.get("SECRET_KEY")
ON_RAILWAY = bool(os.environ.get("RAILWAY_ENVIRONMENT_NAME") or os.environ.get("RAILWAY_ENVIRONMENT"))
# Email: EMAIL_PROVIDER picks the service ("brevo" sends to anyone; "resend" test mode only to yourself)
EMAIL_PROVIDER = os.environ.get("EMAIL_PROVIDER", "resend")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "ParkOS")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM = os.environ.get("RESEND_FROM", "ParkOS <onboarding@resend.dev>")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")      # must be a verified sender in Brevo

# TESTING ONLY: treat Saturday and Sunday as class days so reminders can be tried on a weekend
TEST_WEEKENDS = os.environ.get("PARKOS_TEST_WEEKENDS") == "1"
