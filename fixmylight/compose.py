"""Write the email text. Plain templates by default; optional AI polishing.

The AI is only allowed to rephrase. Facts (location, dates, reference numbers) always
come from the database, and if the AI call fails we silently use the template.
"""
from datetime import datetime, timezone

from .config import Config

FAULT_LABELS = {
    "off": "All lights off / dark",
    "flashing": "Flashing (amber or red)",
    "stuck": "Stuck on one colour",
    "damaged": "Pole or head damaged / knocked over",
    "partial": "Some lights not working",
    "other": "Other",
}


def _days_open(fault) -> int:
    created = datetime.fromisoformat(fault["created_at"])
    return max(0, (datetime.now(timezone.utc) - created).days)


def _facts(fault) -> str:
    lines = [
        f"Location: {fault['intersection']}" + (f", {fault['suburb']}" if fault["suburb"] else ""),
        f"Fault: {FAULT_LABELS.get(fault['fault_type'], fault['fault_type'])}",
    ]
    if fault["lat"] is not None and fault["lng"] is not None:
        lines.append(f"GPS: {fault['lat']:.6f}, {fault['lng']:.6f} "
                     f"(https://maps.google.com/?q={fault['lat']:.6f},{fault['lng']:.6f})")
    if fault["details"]:
        lines.append(f"Details: {fault['details']}")
    lines.append(f"First reported: {fault['created_at'][:10]}")
    if fault["reporter_count"] > 1:
        lines.append(f"Independent reports received: {fault['reporter_count']}")
    if fault["city_reference"]:
        lines.append(f"Your reference number: {fault['city_reference']}")
    lines.append(f"Our tracking ID: {fault['public_id']}")
    return "\n".join(lines)


FOOTER = (
    "\n\n--\nSent by FixMyLight, an open-source community reporting tool. "
    "We send at most one follow-up per working day per fault and stop as soon as it is fixed. "
    "If this fault is already logged or is not your responsibility, simply reply with the "
    "reference number or the correct contact and we will update our records."
)


def subject(fault, kind: str) -> str:
    base = f"Traffic signal fault: {fault['intersection']} [{fault['public_id']}]"
    if fault["city_reference"]:
        base += f" (Ref {fault['city_reference']})"
    return ("Re: " + base) if kind == "followup" else base


def template_body(fault, kind: str) -> str:
    facts = _facts(fault)
    if kind == "initial":
        intro = ("Good day,\n\nI would like to report a faulty traffic signal. "
                 "It is a safety risk for motorists and pedestrians.")
        ask = "Could you please log this fault and reply with a reference number?"
    else:
        n = fault["followups_sent"] + 1
        intro = (f"Good day,\n\nThis is follow-up #{n} on the traffic signal fault below, "
                 f"which has now been reported for {_days_open(fault)} day(s) and is still not working.")
        ask = ("Could you please share the status of the repair and an expected date? "
               "If a repair crew has already been assigned, a short reply is enough and we will note it.")
    return f"{intro}\n\n{facts}\n\n{ask}\n\nKind regards,\nFixMyLight community reporters{FOOTER}"


def ai_body(fault, kind: str) -> str | None:
    if not Config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic  # optional dependency
        client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        draft = template_body(fault, kind)
        msg = client.messages.create(
            model=Config.AI_MODEL,
            max_tokens=600,
            system=("You polish municipal fault-report emails. Keep them short, courteous and "
                    "factual. Never invent facts, dates, reference numbers or threats. Keep every "
                    "line of the facts block and the footer exactly as given. Plain text only."),
            messages=[{"role": "user", "content": f"Polish this email:\n\n{draft}"}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        # Safety net: the facts must survive intact.
        return text if fault["public_id"] in text and fault["intersection"] in text else None
    except Exception:
        return None


def body(fault, kind: str) -> str:
    return ai_body(fault, kind) or template_body(fault, kind)
