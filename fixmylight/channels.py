"""Ready-made links for the other ways to chase a fault: phone, X and WhatsApp.

These open the person's own phone dialler or app with text filled in. Nothing is sent
automatically and no account is needed, which keeps the city's channels free of bot traffic.
"""
from urllib.parse import quote

from .compose import FAULT_LABELS
from .config import Config


def _days(fault) -> str:
    from datetime import datetime, timezone
    d = (datetime.now(timezone.utc) - datetime.fromisoformat(fault["created_at"])).days
    return "today" if d == 0 else f"{d} day{'s' if d != 1 else ''} ago"


def short_text(fault, page_url: str) -> str:
    what = FAULT_LABELS.get(fault["fault_type"], "faulty").split(" (")[0].split(" /")[0].lower()
    where = fault["intersection"] + (f", {fault['suburb']}" if fault["suburb"] else "")
    ref = f" Ref {fault['city_reference']}." if fault["city_reference"] else ""
    people = f" {fault['reporter_count']} people have reported it." if fault["reporter_count"] > 1 else ""
    return (f"Traffic light at {where}: {what}. First reported {_days(fault)}.{ref}{people} "
            f"Track it: {page_url}")


def links(fault, page_url: str) -> dict:
    text = short_text(fault, page_url)
    handles = " ".join("@" + h.lstrip("@") for h in Config.X_HANDLES)
    tel = "".join(c for c in Config.CALL_NUMBER if c.isdigit() or c == "+")
    return {
        "text": text,
        "call_href": f"tel:{tel}",
        "call_number": Config.CALL_NUMBER,
        "call_label": Config.CALL_LABEL,
        "x_href": "https://x.com/intent/post?text=" + quote(f"{handles} {text}".strip()),
        "x_handles": handles,
        "whatsapp_href": "https://wa.me/?text=" + quote(text),
    }
