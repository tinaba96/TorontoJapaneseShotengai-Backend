from fastapi import APIRouter, HTTPException, status
import os

from ..models.contact import ContactRequest
from ..core.email import send_email, admin_emails

router = APIRouter(prefix="/contact", tags=["contact"])

SITE_URL = os.getenv("SITE_URL", "https://www.toronto-shotengai.com")
PROPERTY_NAME = os.getenv("PROPERTY_NAME", "Toronto Japanese Shotengai Rentals")


def _admin_reply_to() -> str:
    emails = admin_emails()
    return os.getenv("REPLY_TO") or (emails[0] if emails else "")


@router.post("")
async def submit_contact(req: ContactRequest):
    """公開: 物件に関する質問を受け付け、admin へ通知＋送信者へ自動返信。"""
    name = (req.name or "").strip()
    message = (req.message or "").strip()
    if not name or not message:
        raise HTTPException(status_code=400, detail="お名前とお問い合わせ内容は必須です。")

    # admin へ通知（ここが失敗したら問い合わせは届かないのでエラーを返す）
    ok = send_email(
        admin_emails(),
        f"【お問い合わせ】{PROPERTY_NAME} に質問が届きました",
        (
            f"物件サイトから新しいお問い合わせが届きました。\n\n"
            f"お名前: {name}\n"
            f"メール: {req.email}\n"
            f"------------------------------\n"
            f"{message}\n"
            f"------------------------------\n\n"
            f"このメールに返信すると {req.email} 宛に送れます。"
        ),
        reply_to=req.email,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="メール送信に失敗しました。時間をおいて再度お試しください。",
        )

    # 送信者へ自動返信（ベストエフォート・失敗してもOK）
    send_email(
        [req.email],
        f"【{PROPERTY_NAME}】お問い合わせありがとうございます",
        (
            f"{name} 様\n\n"
            f"お問い合わせいただきありがとうございます。\n"
            f"以下の内容で受け付けました。担当者より1営業日以内にご返信いたします。\n\n"
            f"------------------------------\n"
            f"{message}\n"
            f"------------------------------\n\n"
            f"物件の詳細はこちら:\n{SITE_URL}\n\n"
            f"{PROPERTY_NAME}"
        ),
        reply_to=_admin_reply_to(),
    )
    return {"ok": True}
