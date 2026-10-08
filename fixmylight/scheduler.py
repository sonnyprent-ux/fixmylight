"""Built-in daily scheduler, so the hosted web app needs no separate cron job.

Runs the follow-up job once each working day at FIXMYLIGHT_RUN_AT (Johannesburg time).
A file lock ensures only one process sends, even if the server starts several workers.
"""
import fcntl
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import db
from .config import Config
from .followup import run

log = logging.getLogger("fixmylight.scheduler")
TZ = ZoneInfo("Africa/Johannesburg")


def next_run(after: datetime, at: str = "07:10") -> datetime:
    """Next HH:MM in Johannesburg strictly after `after` (weekends handled by the job itself)."""
    hh, mm = (int(x) for x in at.split(":"))
    local = after.astimezone(TZ)
    candidate = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if candidate <= local:
        candidate += timedelta(days=1)
    return candidate


def _loop(at: str):
    while True:
        target = next_run(datetime.now(TZ), at)
        time.sleep(max(1, (target - datetime.now(TZ)).total_seconds()))
        try:
            conn = db.connect(Config.DATABASE)
            log.info("follow-up run: %s", run(conn))
            conn.close()
        except Exception:  # never let the scheduler thread die
            log.exception("follow-up run failed")


_started = False


def start():
    """Start once per machine. Returns True if this process owns the scheduler."""
    global _started
    if _started or not Config.SCHEDULER:
        return False
    lock_path = os.path.abspath(Config.DATABASE) + ".scheduler.lock"
    fh = open(lock_path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return False  # another worker already runs it
    _started = True
    t = threading.Thread(target=_loop, args=(Config.RUN_AT,), daemon=True, name="fixmylight-scheduler")
    t._lock_fh = fh  # keep the lock for the life of the process
    t.start()
    log.info("scheduler started; daily run at %s Africa/Johannesburg", Config.RUN_AT)
    return True
