-- ParkOS database schema (PostgreSQL, no PostGIS needed).
--
-- What lives where:
--   * Campus reference data stays as files in the repo: lots and buildings (data/*.geojson),
--     prices (data/zone_rates.csv) and the academic calendar (parking/academic_calendar.py).
--     It's the same for every user, changes a few times a year, and is small enough to keep in memory.
--   * Everything users create, and everything the app records, lives here: one row-set per user.
--
-- Every user table has user_id → users(id) ON DELETE CASCADE: deleting an account deletes its data.

-- ===== Accounts =============================================================================

-- One row per account. Users sign up with an email and password.
-- The password itself is NEVER stored: only a slow, salted hash (werkzeug's scrypt), which can
-- check a password but can't be turned back into one.
CREATE TABLE users (
    id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email         text NOT NULL CHECK (length(email) <= 254 AND email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    password_hash text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);
-- Unique ignoring capitals: "Sukhman@ucdavis.edu" and "sukhman@ucdavis.edu" are the same account
CREATE UNIQUE INDEX users_email_unique ON users (lower(email));

-- One-to-one with users: user_id is both the primary key and the link, so each user has at most one row.
-- email here is where reminders go: it starts as the sign-in email and can be changed separately.
-- lead_minutes and walk_limit_min aren't shown in the app right now; they keep their defaults.
CREATE TABLE user_settings (
    user_id           bigint PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    email             text CHECK (email IS NULL OR email ~ '^[^@\s]+@[^@\s]+\.[^@\s]+$'),   -- where reminders go
    affiliation       text NOT NULL DEFAULT 'student' CHECK (affiliation IN ('student', 'staff', 'visitor')),
    reminders_enabled boolean NOT NULL DEFAULT true,
    lead_minutes      smallint NOT NULL DEFAULT 30 CHECK (lead_minutes BETWEEN 0 AND 180),
    walk_limit_min    smallint NOT NULL DEFAULT 10 CHECK (walk_limit_min BETWEEN 1 AND 30),
    priority          text NOT NULL DEFAULT 'best' CHECK (priority IN ('best', 'cheapest', 'closest')),
    channel           text NOT NULL DEFAULT 'email' CHECK (channel IN ('email'))
);

-- ===== Each user's schedule =================================================================

CREATE TABLE schedule_entries (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id     bigint NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    course      text NOT NULL CHECK (length(btrim(course)) BETWEEN 1 AND 80),   -- "EEC 170 Lecture"
    days        smallint[] NOT NULL                                             -- {1,3,5} = Mon, Wed, Fri
                CHECK (cardinality(days) >= 1 AND days <@ ARRAY[1, 2, 3, 4, 5, 6, 7]::smallint[]),
    start_time  time NOT NULL,                                                  -- campus local time
    end_time    time CHECK (end_time IS NULL OR end_time > start_time),
    -- The campus map's building id (OBJECTID). No foreign key: buildings live in data/ucd_buildings.geojson,
    -- and the API checks the id exists before saving. NULL = no building (the reminder still goes out).
    building_id integer,
    room        text,                                                           -- "1316", from an imported file
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX schedule_entries_user ON schedule_entries (user_id);

-- ===== Reminders ============================================================================

-- A time the user chose for one day. On a class day it replaces the automatic time;
-- on any other day (weekend, holiday) it creates a reminder. At most one per user per day.
CREATE TABLE custom_reminders (
    user_id       bigint NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    reminder_date date NOT NULL,
    remind_at     time NOT NULL,
    set_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, reminder_date)
);

-- What the reminder job sent. The primary key (user_id, reminder_date) means ONE row per user per day,
-- so even if the job runs twice it can't send the same day twice: the second INSERT fails.
-- A custom reminder re-timed after it was sent UPDATEs this row and is sent again.
CREATE TABLE reminders_sent (
    user_id       bigint NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    reminder_date date NOT NULL,
    remind_at     time NOT NULL,                    -- the time it was due (to spot re-timing)
    custom        boolean NOT NULL DEFAULT false,
    status        text NOT NULL CHECK (status IN ('sending', 'sent', 'failed')),
    to_email      text,
    provider_id   text,                             -- Brevo/Resend's id for the email
    error         text,                             -- why it failed, if it did
    sent_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, reminder_date)
);

-- ===== Shared app data (not per user) =======================================================

-- Google Routes answers, kept so each one is paid for once. Shared by all users:
-- a walk from Lot 5 to Olson Hall is the same for everyone.
-- (A database table rather than a file because hosting platforms wipe local files on each deploy.)
CREATE TABLE route_cache (
    cache_key  text PRIMARY KEY,                    -- "walk:2223>b439", "drive:p38.5440,-121.7405>2223", ...
    kind       text NOT NULL CHECK (kind IN ('walk', 'drive', 'walk_route', 'drive_route')),
    seconds    integer NOT NULL CHECK (seconds >= 0),
    metres     integer NOT NULL CHECK (metres >= 0),
    path       jsonb,                               -- [[lat, lng], ...] for drawn routes, NULL otherwise
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Requests made to paid APIs each month, so the app stops before the free tier runs out.
CREATE TABLE api_usage (
    provider text NOT NULL,                         -- 'google_routes'
    month    char(7) NOT NULL CHECK (month ~ '^\d{4}-\d{2}$'),   -- '2026-10'
    requests integer NOT NULL DEFAULT 0 CHECK (requests >= 0),
    PRIMARY KEY (provider, month)
);
