from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import os

from ..models.viewing import (
    ViewingSlot,
    ViewingSlotCreate,
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
@router.get("/slots", response_model=List[ViewingSlot])
async def list_slots():
    """Public: list upcoming viewing slots with their current booking counts."""
    return await ViewingCRUD.get_slots(upcoming_only=True)


@router.post("/bookings", response_model=ViewingBooking, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: ViewingBookingCreate,
    current_user=Depends(get_current_user),
):
    """Authenticated (Google-logged-in) users book a viewing slot."""
    booking, cancel_token = await ViewingCRUD.create_booking(booking_in)

    cancel_url = f"{FRONTEND_URL}/viewing/cancel?token={cancel_token}"
    when = booking.starts_at or ""

    # Confirmation to the visitor (best-effort).
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
    # Notification to admins (best-effort).
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
    """Public: cancel a booking using the token from the confirmation email."""
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
@router.post("/slots", response_model=ViewingSlot, status_code=status.HTTP_201_CREATED)
async def create_slot(slot: ViewingSlotCreate, admin=Depends(get_admin_user)):
    """Admin: register an available 30-minute viewing slot."""
    return await ViewingCRUD.create_slot(slot)


@router.delete("/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(slot_id: str, admin=Depends(get_admin_user)):
    """Admin: delete a slot (only if it has no active bookings)."""
    ok = await ViewingCRUD.delete_slot(slot_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found.")
    return None


@router.get("/bookings", response_model=List[ViewingBooking])
async def list_bookings(admin=Depends(get_admin_user)):
    """Admin: see who is coming and when."""
    return await ViewingCRUD.get_bookings()
