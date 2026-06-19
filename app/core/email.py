"""
Simple, best-effort email sending using the Python standard library (smtplib).

Design goals:
- Zero hard dependency on a third-party email service.
- Email failures must NEVER break the booking flow — every function is
  exception-safe and returns a boolean instead of raising.
- If SMTP is not configured (no SMTP_HOST / SMTP_FROM), the email is skipped
  and logged, so the rest of the app keeps working during early development.
"""
import os
import ssl
import smtplib
from email.message import EmailMessage
from typing import List


def admin_emails() -> List[str]:
    """Return the list of admin email addresses from the ADMIN_EMAILS env var."""
    raw = os.getenv("ADMIN_EMAILS", "")
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


def _smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def send_email(to: List[str], subject: str, body: str) -> bool:
    """
    Send a plain-text email to the given recipients (best-effort).
    Returns True if the email was actually sent, False otherwise.
    Never raises.
    """
    recipients = [t for t in to if t]
    if not recipients:
        return False

    if not _smtp_configured():
        print(f"[email:skip] SMTP not configured. Would send to {recipients}: {subject}")
        return False

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM")

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls(context=context)
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as ex:  # noqa: BLE001 - email must not break the request
        print(f"[email:error] Failed to send '{subject}' to {recipients}: {ex}")
        return False
