"""The database: Postgres, reached through DATABASE_URL (Railway sets it; locally it's in backend/.env).

    connection()    borrow a connection from the pool:  with connection() as conn: conn.execute(...)
    migrate.py      creates the tables from schema.sql the first time the app starts
    users.py ...    one file per group of tables, each a handful of plain SQL queries

A pool keeps a few connections open and lends them out, because opening a new Postgres connection
for every request is slow. Leaving the `with` block commits the transaction (or rolls it back
if an error was raised) and returns the connection to the pool.
"""
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

import config

_pool = None


def connection():
    global _pool
    if _pool is None:
        if not config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set (add it to backend/.env, or the Railway service's variables)")
        # dict_row: each row comes back as {"column": value} instead of a tuple
        _pool = ConnectionPool(config.DATABASE_URL, min_size=1, max_size=5, kwargs={"row_factory": dict_row})
    return _pool.connection()
