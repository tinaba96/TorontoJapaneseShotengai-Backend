from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import os

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
    when = booking.starts_at or ""

    send_email(
        [booking.email],
        "【内見予約】ご予約を受け付けました",
        (
            f"{booking.name} 様\n\n"
            f"内見のご予約を受け付けました。\n"
            f"日時(UTC): {when}\n\n"
            f"ご都合が悪くなった場合は、以下のリンクからキャンセルできます:\n"
            f"{cancel_url}\n\n"
            f"当日お会いできるのを楽しみにしております。"
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
            f"日時(UTC): {when}"
        ),
    )
    return booking


@router.post("/cancel", response_model=ViewingBooking)
async def cancel_booking(req: CancelRequest):
    """公開: 確認メールのトークンで予約をキャンセル。"""
    booking = await ViewingCRUD.cancel_by_token(req.token)
    when = booking.starts_at or ""
    send_email(
        admin_emails(),
        "【内見予約】予約がキャンセルされました",
        (
            f"以下の内見予約がキャンセルされました。\n\n"
            f"名前: {booking.name}\n"
            f"メール: {booking.email}\n"
            f"日時(UTC): {when}"
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
