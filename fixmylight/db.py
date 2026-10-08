"""SQLite storage. One row per fault; reporters who see the same fault are merged into it."""
import math
import secrets
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS faults (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    public_id       TEXT UNIQUE NOT NULL,
    intersection    TEXT NOT NULL,
    suburb          TEXT,
    lat             REAL,
    lng             REAL,
    fault_type      TEXT NOT NULL,
    details         TEXT,
    status          TEXT NOT NULL DEFAULT 'open',   -- open | fixed | paused | escalated
    city_reference  TEXT,                           -- reference number the city gives back
    thread_msgid    TEXT,                           -- Message-ID of first email, for threading
    followups_sent  INTEGER NOT NULL DEFAULT 0,
    reporter_count  INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    last_emailed_at TEXT,
    fixed_at        TEXT,
    manage_token    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS emails (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    fault_id  INTEGER NOT NULL REFERENCES faults(id),
    kind      TEXT NOT NULL,          -- initial | followup | resolved
    subject   TEXT NOT NULL,
    body      TEXT NOT NULL,
    msgid     TEXT,
    sent_at   TEXT NOT NULL,
    dry_run   INTEGER NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def distance_m(lat1, lng1, lat2, lng2) -> float:
    r = 6_371_000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def find_duplicate(conn, intersection, lat, lng, radius_m):
    """An open fault at the same place counts as the same fault."""
    rows = conn.execute("SELECT * FROM faults WHERE status IN ('open','escalated')").fetchall()
    key = " ".join(intersection.lower().split())
    for row in rows:
        if " ".join(row["intersection"].lower().split()) == key:
            return row
        if None not in (lat, lng, row["lat"], row["lng"]) and \
                distance_m(lat, lng, row["lat"], row["lng"]) <= radius_m:
            return row
    return None


def create_fault(conn, *, intersection, suburb, lat, lng, fault_type, details):
    public_id = "FML-" + secrets.token_hex(3).upper()
    token = secrets.token_urlsafe(16)
    cur = conn.execute(
        """INSERT INTO faults (public_id, intersection, suburb, lat, lng, fault_type,
           details, created_at, manage_token) VALUES (?,?,?,?,?,?,?,?,?)""",
        (public_id, intersection.strip(), suburb, lat, lng, fault_type, details, now(), token),
    )
    conn.commit()
    return conn.execute("SELECT * FROM faults WHERE id=?", (cur.lastrowid,)).fetchone()


def add_reporter(conn, fault_id):
    conn.execute("UPDATE faults SET reporter_count = reporter_count + 1 WHERE id=?", (fault_id,))
    conn.commit()


def get(conn, public_id):
    return conn.execute("SELECT * FROM faults WHERE public_id=?", (public_id,)).fetchone()


def set_status(conn, fault_id, status):
    fixed_at = now() if status == "fixed" else None
    conn.execute("UPDATE faults SET status=?, fixed_at=? WHERE id=?", (status, fixed_at, fault_id))
    conn.commit()


def set_reference(conn, fault_id, ref):
    conn.execute("UPDATE faults SET city_reference=? WHERE id=?", (ref.strip() or None, fault_id))
    conn.commit()


def log_email(conn, fault_id, kind, subject, body, msgid, dry_run):
    conn.execute(
        "INSERT INTO emails (fault_id, kind, subject, body, msgid, sent_at, dry_run) VALUES (?,?,?,?,?,?,?)",
        (fault_id, kind, subject, body, msgid, now(), int(dry_run)),
    )
    if kind == "initial":
        conn.execute("UPDATE faults SET thread_msgid=?, last_emailed_at=? WHERE id=?",
                     (msgid, now(), fault_id))
    elif kind == "followup":
        conn.execute("UPDATE faults SET followups_sent=followups_sent+1, last_emailed_at=? WHERE id=?",
                     (now(), fault_id))
    conn.commit()
