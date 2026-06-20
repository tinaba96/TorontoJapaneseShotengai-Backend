from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
import os

try:
    from zoneinfo import ZoneInfo
    TORONTO_TZ = ZoneInfo("America/Toronto")
    TOKYO_TZ = ZoneInfo("Asia/Tokyo")
except Exception:  # zoneinfo/tzdata が無い環境ではUTC表記にフォールバック
    TORONTO_TZ = None
    TOKYO_TZ = None

_WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]


def format_toronto(iso_str: str) -> str:
    """
    UTCのISO文字列を、トロント時間（日本時間を括弧補足）に整形。
    例: 2026年6月21日(日) 14:00（トロント時間 / 日本時間 6月22日(月) 03:00）
    """
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if TORONTO_TZ is None:
            return f"{iso_str} (UTC)"
        t = dt.astimezone(TORONTO_TZ)
        tw = _WEEKDAYS_JA[t.weekday()]
        base = f"{t.year}年{t.month}月{t.day}日({tw}) {t.strftime('%H:%M')}"
        if TOKYO_TZ is not None:
            j = dt.astimezone(TOKYO_TZ)
            jw = _WEEKDAYS_JA[j.weekday()]
            return (
                f"{base}（トロント時間 / 日本時間 "
                f"{j.month}月{j.day}日({jw}) {j.strftime('%H:%M')}）"
            )
        return f"{base}（トロント時間）"
    except Exception:
        return iso_str

from ..models.viewing import (
    AvailabilityWindow,
    AvailabilityWindowCreate,
    AvailabilitySlot,
    ViewingBooking,
    ViewingBookingCreate,
    CancelRequest,
)
from ..crud.viewing import ViewingCRUD
from ..core.security import get_admin_user, get_current_user
from ..core.email import send_email, admin_emails

router = APIRouter(prefix="/viewing", tags=["viewing"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
# メール文面で使う公開サイトURLと物件名（env で上書き可）
SITE_URL = os.getenv("SITE_URL", "https://www.toronto-shotengai.com")
PROPERTY_NAME = os.getenv("PROPERTY_NAME", "Toronto Japanese Shotengai Rentals")


# ----- Public ------------------------------------------------------------
@router.get("/slots", response_model=List[AvailabilitySlot])
async def list_slots():
    """公開: 登録された期間から自動生成した30分スロット一覧（予約数つき）。"""
    return await ViewingCRUD.get_available_slots()


@router.post("/bookings", response_model=ViewingBooking, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: ViewingBookingCreate,
    current_user=Depends(get_current_user),
):
    """Googleログイン済みユーザーが、選択した30分枠を予約する。"""
    booking, cancel_token = await ViewingCRUD.create_booking(booking_in)

    cancel_url = f"{FRONTEND_URL}/viewing/cancel?token={cancel_token}"
    when = format_toronto(booking.starts_at)

    send_email(
        [booking.email],
        f"【内見予約】{PROPERTY_NAME} のご予約を受け付けました",
        (
            f"{booking.name} 様\n\n"
            f"この度は「{PROPERTY_NAME}」の内見をご予約いただきありがとうございます。\n"
            f"以下の内容でお申し込みを受け付けました。\n\n"
            f"▼ ご予約内容\n"
            f"物件: {PROPERTY_NAME}\n"
            f"内見日時: {when}\n\n"
            f"物件の詳細はこちら:\n"
            f"{SITE_URL}\n\n"
            f"ご都合が悪くなった場合は、以下のリンクからいつでもキャンセルできます:\n"
            f"{cancel_url}\n\n"
            f"当日お会いできるのを楽しみにしております。\n"
            f"{PROPERTY_NAME}"
        ),
    )
    send_email(
        admin_emails(),
        "【内見予約】新しい予約が入りました",
        (
            f"新しい内見予約が入りました。\n\n"
            f"名前: {booking.name}\n"
            f"メール: {booking.email}\n"
            f"電話: {booking.phone or '-'}\n"
            f"日時: {when}"
        ),
    )
    return booking


@router.post("/cancel", response_model=ViewingBooking)
async def cancel_booking(req: CancelRequest):
    """公開: 確認メールのトークンで予約をキャンセル。"""
    booking = await ViewingCRUD.cancel_by_token(req.token)
    when = format_toronto(booking.starts_at)

    # 予約者本人へキャンセル確認
    send_email(
        [booking.email],
        f"【内見予約】{PROPERTY_NAME} のご予約をキャンセルしました",
        (
            f"{booking.name} 様\n\n"
            f"以下の内見予約をキャンセルしました。\n\n"
            f"▼ キャンセルした予約\n"
            f"物件: {PROPERTY_NAME}\n"
            f"内見日時: {when}\n\n"
            f"またのご予約をお待ちしております。\n"
            f"{SITE_URL}\n\n"
            f"{PROPERTY_NAME}"
        ),
    )
    # admin へ通知
    send_email(
        admin_emails(),
        "【内見予約】予約がキャンセルされました",
        (
            f"以下の内見予約がキャンセルされました。\n\n"
            f"名前: {booking.name}\n"
            f"メール: {booking.email}\n"
            f"日時: {when}"
        ),
    )
    return booking


# ----- Admin -------------------------------------------------------------
@router.post("/windows", response_model=AvailabilityWindow, status_code=status.HTTP_201_CREATED)
async def create_window(window: AvailabilityWindowCreate, admin=Depends(get_admin_user)):
    """Admin: 内見可能な期間（開始〜終了）を登録。この範囲の30分枠が選べるようになる。"""
    return await ViewingCRUD.create_window(window)


@router.get("/windows", response_model=List[AvailabilityWindow])
async def list_windows(admin=Depends(get_admin_user)):
    """Admin: 登録済みの可能期間一覧。"""
    return await ViewingCRUD.get_windows(upcoming_only=False)


@router.delete("/windows/{window_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_window(window_id: str, admin=Depends(get_admin_user)):
    """Admin: 期間を削除（範囲内に有効な予約があると 409）。"""
    ok = await ViewingCRUD.delete_window(window_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Window not found.")
    return None


@router.get("/bookings", response_model=List[ViewingBooking])
async def list_bookings(admin=Depends(get_admin_user)):
    """Admin: 予約一覧（誰がいつ来るか）。"""
    return await ViewingCRUD.get_bookings()
