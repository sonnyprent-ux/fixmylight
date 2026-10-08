"""Send email over SMTP, threaded so every follow-up lands in the same conversation."""
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid, formatdate

from .config import Config


def send(subject: str, body: str, in_reply_to: str | None = None) -> tuple[str, bool]:
    msg = EmailMessage()
    msg["From"] = Config.FROM
    msg["To"] = ", ".join(Config.TO)
    if Config.CC:
        msg["Cc"] = ", ".join(Config.CC)
    if Config.REPLY_TO:
        msg["Reply-To"] = Config.REPLY_TO
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    domain = Config.FROM.split("@")[-1] or "fixmylight.local"
    msg["Message-ID"] = make_msgid(domain=domain)
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)

    if Config.DRY_RUN or not Config.SMTP_HOST:
        print("=" * 70 + "\n[DRY RUN — not sent]\n" + msg.as_string() + "\n")
        return msg["Message-ID"], True

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=30) as s:
        if Config.SMTP_STARTTLS:
            s.starttls()
        if Config.SMTP_USER:
            s.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        s.send_message(msg)
    return msg["Message-ID"], False
