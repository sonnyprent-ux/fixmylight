"""All settings come from environment variables (see .env.example)."""
import os


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


class Config:
    DATABASE = os.getenv("FIXMYLIGHT_DB", "fixmylight.sqlite3")
    SECRET_KEY = os.getenv("FIXMYLIGHT_SECRET", "change-me")
    BASE_URL = os.getenv("FIXMYLIGHT_BASE_URL", "http://localhost:5000")
    ADMIN_TOKEN = os.getenv("FIXMYLIGHT_ADMIN_TOKEN", "")

    # Who receives reports. JRA (Johannesburg Roads Agency) maintains city traffic
    # signals. Always verify these before going live — see README.
    TO = _list("FIXMYLIGHT_TO", "hotline@jra.org.za")
    CC = _list("FIXMYLIGHT_CC", "")
    FROM = os.getenv("FIXMYLIGHT_FROM", "fixmylight@example.org")
    REPLY_TO = os.getenv("FIXMYLIGHT_REPLY_TO", "")

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_STARTTLS = _bool("SMTP_STARTTLS", True)

    # Dry run: print emails instead of sending. ON by default so nobody spams the city by accident.
    DRY_RUN = _bool("FIXMYLIGHT_DRY_RUN", True)

    # Guardrails for follow-ups
    FOLLOWUP_HOURS = int(os.getenv("FIXMYLIGHT_FOLLOWUP_HOURS", "24"))
    MAX_FOLLOWUPS = int(os.getenv("FIXMYLIGHT_MAX_FOLLOWUPS", "30"))
    SKIP_WEEKENDS = _bool("FIXMYLIGHT_SKIP_WEEKENDS", True)
    DEDUP_RADIUS_M = int(os.getenv("FIXMYLIGHT_DEDUP_RADIUS_M", "75"))

    # Built-in scheduler for the hosted app (turn off if you prefer an external cron job)
    SCHEDULER = _bool("FIXMYLIGHT_SCHEDULER", False)
    RUN_AT = os.getenv("FIXMYLIGHT_RUN_AT", "07:10")  # Africa/Johannesburg time

    # Other channels shown on the one-stop status page
    CITY_NAME = os.getenv("FIXMYLIGHT_CITY_NAME", "City of Johannesburg")
    CALL_NUMBER = os.getenv("FIXMYLIGHT_CALL_NUMBER", "0860 562 874")
    CALL_LABEL = os.getenv("FIXMYLIGHT_CALL_LABEL", "Joburg Connect")
    X_HANDLES = _list("FIXMYLIGHT_X_HANDLES", "CityofJoburgZA")

    # Optional AI drafting (falls back to plain templates if unset)
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    AI_MODEL = os.getenv("FIXMYLIGHT_AI_MODEL", "claude-haiku-5-5")
