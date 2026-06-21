"""
Best-effort email sending.

優先順位:
  1) Resend (HTTP API / 443番ポート) ... RESEND_API_KEY があればこれを使う。
     RenderのようにSMTP(587)が塞がれている環境でも送れる。
  2) SMTP (smtplib) ............ SMTP_HOST + SMTP_FROM があればフォールバック。
  3) どちらも無ければスキップ（ログのみ）。

どの経路でも失敗は例外を投げず False を返す（予約フローを止めない）。
"""
import os
import ssl
import smtplib
from email.message import EmailMessage
from typing import List, Optional


def admin_emails() -> List[str]:
    """ADMIN_EMAILS(カンマ区切り) を小文字・トリムして返す。"""
    raw = os.getenv("ADMIN_EMAILS", "")
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


def _email_from() -> str:
    # Resend/SMTP 共通の送信元。EMAIL_FROM を優先、無ければ SMTP_FROM。
    return os.getenv("EMAIL_FROM") or os.getenv("SMTP_FROM") or ""


def _send_via_resend(
    recipients: List[str], subject: str, body: str, reply_to: Optional[str] = None
) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    sender = _email_from()
    if not api_key or not sender:
        return False
    try:
        import requests  # requirements に同梱済み

        payload = {
            "from": sender,
            "to": recipients,
            "subject": subject,
            "text": body,
        }
        if reply_to:
            payload["reply_to"] = reply_to

        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return True
        print(f"[email:error] Resend failed {resp.status_code}: {resp.text}")
        return False
    except Exception as ex:  # noqa: BLE001
        print(f"[email:error] Resend exception: {ex}")
        return False


def _smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and _email_from())


def _send_via_smtp(
    recipients: List[str], subject: str, body: str, reply_to: Optional[str] = None
) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = _email_from()
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls(context=context)
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as ex:  # noqa: BLE001
        print(f"[email:error] SMTP failed to send '{subject}' to {recipients}: {ex}")
        return False


def send_email(
    to: List[str], subject: str, body: str, reply_to: Optional[str] = None
) -> bool:
    """
    プレーンテキストメールを送る（ベストエフォート）。送れたら True。
    reply_to を渡すと、受信者が「返信」したときの宛先になる。
    Resend → SMTP の順に試す。どちらも未設定ならスキップ。
    """
    recipients = [t for t in to if t]
    if not recipients:
        return False

    # 1) Resend (HTTP)
    if os.getenv("RESEND_API_KEY") and _email_from():
        if _send_via_resend(recipients, subject, body, reply_to):
            return True
        # Resendが失敗してもSMTP設定があれば続けて試す

    # 2) SMTP
    if _smtp_configured():
        return _send_via_smtp(recipients, subject, body, reply_to)

    print(f"[email:skip] No email transport configured. Would send to {recipients}: {subject}")
    return False
