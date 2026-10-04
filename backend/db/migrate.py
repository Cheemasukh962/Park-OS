"""Create the tables from schema.sql if they don't exist yet. Runs when the app starts.

Simple on purpose: it only handles "empty database → all tables". A later change to an existing
table would need a real migration tool (e.g. Alembic) or a hand-written ALTER TABLE.
"""
from pathlib import Path

from db import connection

SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def ensure_schema():
    with connection() as conn:
        exists = conn.execute("SELECT to_regclass('public.users') AS t").fetchone()["t"]
        if exists is None:
            conn.execute(SCHEMA.read_text())          # every CREATE in one transaction: all or nothing
            print("[db] created tables from schema.sql", flush=True)
