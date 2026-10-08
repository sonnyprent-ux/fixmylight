"""The daily job: send one polite follow-up per open fault, with guardrails."""
from datetime import datetime, timedelta, timezone

from . import compose, db, mailer
from .config import Config


def send_initial(conn, fault):
    subj, text = compose.subject(fault, "initial"), compose.body(fault, "initial")
    msgid, dry = mailer.send(subj, text)
    db.log_email(conn, fault["id"], "initial", subj, text, msgid, dry)


def is_due(fault, at: datetime) -> tuple[bool, str]:
    if fault["status"] != "open":
        return False, f"status is {fault['status']}"
    if Config.SKIP_WEEKENDS and at.astimezone().weekday() >= 5:
        return False, "weekend"
    if fault["followups_sent"] >= Config.MAX_FOLLOWUPS:
        return False, "max follow-ups reached"
    if fault["last_emailed_at"]:
        last = datetime.fromisoformat(fault["last_emailed_at"])
        # small grace window so a daily cron at the same time is never skipped
        if at - last < timedelta(hours=Config.FOLLOWUP_HOURS) - timedelta(minutes=30):
            return False, "emailed recently"
    return True, "due"


def run(conn, at: datetime | None = None) -> dict:
    at = at or datetime.now(timezone.utc)
    sent, skipped, escalated = [], [], []
    for fault in conn.execute("SELECT * FROM faults WHERE status='open'").fetchall():
        if fault["followups_sent"] >= Config.MAX_FOLLOWUPS:
            db.set_status(conn, fault["id"], "escalated")
            escalated.append(fault["public_id"])
            continue
        due, why = is_due(fault, at)
        if not due:
            skipped.append((fault["public_id"], why))
            continue
        subj, text = compose.subject(fault, "followup"), compose.body(fault, "followup")
        msgid, dry = mailer.send(subj, text, in_reply_to=fault["thread_msgid"])
        db.log_email(conn, fault["id"], "followup", subj, text, msgid, dry)
        sent.append(fault["public_id"])
    return {"sent": sent, "skipped": skipped, "escalated": escalated}
