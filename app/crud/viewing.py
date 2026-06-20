from app.crud.database import db
from fastapi import HTTPException, status
from app.models.viewing import (
    AvailabilityWindow,
    AvailabilityWindowCreate,
    AvailabilitySlot,
    ViewingBooking,
    ViewingBookingCreate,
)
from typing import List, Tuple
from uuid import uuid4
from datetime import datetime, timedelta, timezone

SLOT_MINUTES = 30


def _parse_iso(s: str) -> datetime:
    """ISO文字列(末尾Zも許容)を UTC・秒精度の aware datetime に正規化。"""
    s = s.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def _native(neo_dt) -> datetime:
    """neo4j DateTime -> python aware datetime(UTC・秒精度)。"""
    dt = neo_dt.to_native()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0)


class ViewingCRUD:
    # ===== Availability windows (admin) =====
    @staticmethod
    async def create_window(w: AvailabilityWindowCreate) -> AvailabilityWindow:
        start = _parse_iso(w.starts_at)
        end = _parse_iso(w.ends_at)
        if end <= start:
            raise HTTPException(status_code=400, detail="End must be after start.")
        if (end - start) < timedelta(minutes=SLOT_MINUTES):
            raise HTTPException(status_code=400, detail="Window must be at least 30 minutes.")
        with db.get_session() as session:
            wid = str(uuid4())
            rec = session.run(
                """
                CREATE (w:AvailabilityWindow {
                    id: $id,
                    starts_at: datetime($s),
                    ends_at: datetime($e),
                    created_at: datetime()
                })
                RETURN w
                """,
                id=wid, s=start.isoformat(), e=end.isoformat(),
            ).single()
            if not rec:
                raise HTTPException(status_code=500, detail="Failed to create window.")
            w_ = rec["w"]
            return AvailabilityWindow(
                id=w_["id"],
                starts_at=_native(w_["starts_at"]).isoformat(),
                ends_at=_native(w_["ends_at"]).isoformat(),
                created_at=_native(w_["created_at"]).isoformat(),
            )

    @staticmethod
    async def get_windows(upcoming_only: bool = True) -> List[AvailabilityWindow]:
        with db.get_session() as session:
            where = "WHERE w.ends_at >= datetime()" if upcoming_only else ""
            res = session.run(
                f"MATCH (w:AvailabilityWindow) {where} RETURN w ORDER BY w.starts_at ASC"
            )
            out = []
            for r in res:
                w_ = r["w"]
                out.append(
                    AvailabilityWindow(
                        id=w_["id"],
                        starts_at=_native(w_["starts_at"]).isoformat(),
                        ends_at=_native(w_["ends_at"]).isoformat(),
                        created_at=_native(w_["created_at"]).isoformat(),
                    )
                )
            return out

    @staticmethod
    async def delete_window(window_id: str) -> bool:
        """期間内に有効な予約があれば削除拒否(409)。存在しなければ False。"""
        with db.get_session() as session:
            rec = session.run(
                "MATCH (w:AvailabilityWindow {id: $id}) RETURN w", id=window_id
            ).single()
            if not rec:
                return False
            w_ = rec["w"]
            start = _native(w_["starts_at"])
            end = _native(w_["ends_at"])
            cnt = session.run(
                """
                MATCH (b:ViewingBooking {status: 'active'})
                WHERE b.starts_at >= datetime($s) AND b.starts_at < datetime($e)
                RETURN count(b) AS c
                """,
                s=start.isoformat(), e=end.isoformat(),
            ).single()["c"]
            if cnt > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete a window that has active bookings.",
                )
            session.run(
                "MATCH (w:AvailabilityWindow {id: $id}) DETACH DELETE w", id=window_id
            )
            return True

    # ===== Derived 30-min slots (公開) =====
    @staticmethod
    async def get_available_slots() -> List[AvailabilitySlot]:
        windows = await ViewingCRUD.get_windows(upcoming_only=True)

        # 有効予約の開始時刻ごとの件数
        counts = {}
        with db.get_session() as session:
            res = session.run(
                "MATCH (b:ViewingBooking {status: 'active'}) RETURN b.starts_at AS s"
            )
            for r in res:
                if r["s"] is None:
                    continue
                key = _native(r["s"]).isoformat()
                counts[key] = counts.get(key, 0) + 1

        now = datetime.now(timezone.utc).replace(microsecond=0)
        step = timedelta(minutes=SLOT_MINUTES)
        seen = set()
        slots: List[AvailabilitySlot] = []
        for w in windows:
            start = _parse_iso(w.starts_at)
            end = _parse_iso(w.ends_at)
            cur = start
            while cur + step <= end:
                key = cur.isoformat()
                if cur >= now and key not in seen:
                    seen.add(key)
                    slots.append(AvailabilitySlot(starts_at=key, booking_count=counts.get(key, 0)))
                cur += step
        slots.sort(key=lambda s: s.starts_at)
        return slots

    # ===== Bookings =====
    @staticmethod
    async def create_booking(b: ViewingBookingCreate) -> Tuple[ViewingBooking, str]:
        chosen = _parse_iso(b.starts_at)

        # 選択枠が「現在提示中の有効スロット」に含まれるか検証
        valid = {s.starts_at for s in await ViewingCRUD.get_available_slots()}
        if chosen.isoformat() not in valid:
            raise HTTPException(status_code=400, detail="Selected time is not available.")

        with db.get_session() as session:
            existing = session.run(
                "MATCH (b:ViewingBooking {email: $email, status: 'active'}) RETURN b LIMIT 1",
                email=b.email,
            ).single()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="You already have an active booking. Please cancel it before booking another time.",
                )

            booking_id = str(uuid4())
            cancel_token = str(uuid4())
            rec = session.run(
                """
                CREATE (b:ViewingBooking {
                    id: $id,
                    starts_at: datetime($s),
                    name: $name,
                    email: $email,
                    phone: $phone,
                    status: 'active',
                    cancel_token: $token,
                    created_at: datetime()
                })
                RETURN b
                """,
                id=booking_id, s=chosen.isoformat(), name=b.name, email=b.email,
                phone=b.phone, token=cancel_token,
            ).single()
            if not rec:
                raise HTTPException(status_code=500, detail="Failed to create booking.")
            bd = rec["b"]
            booking = ViewingBooking(
                id=bd["id"],
                starts_at=_native(bd["starts_at"]).isoformat(),
                name=bd["name"],
                email=bd["email"],
                phone=bd.get("phone"),
                status=bd["status"],
                created_at=_native(bd["created_at"]).isoformat(),
            )
            return booking, cancel_token

    @staticmethod
    async def get_bookings() -> List[ViewingBooking]:
        with db.get_session() as session:
            res = session.run(
                """
                MATCH (b:ViewingBooking)
                RETURN b
                ORDER BY b.starts_at ASC, b.created_at ASC
                """
            )
            out = []
            for r in res:
                bd = r["b"]
                starts_at = bd.get("starts_at")
                out.append(
                    ViewingBooking(
                        id=bd["id"],
                        starts_at=_native(starts_at).isoformat() if starts_at else None,
                        name=bd["name"],
                        email=bd["email"],
                        phone=bd.get("phone"),
                        status=bd["status"],
                        created_at=_native(bd["created_at"]).isoformat(),
                        address_sent=bool(bd.get("address_sent_at")),
                    )
                )
            return out

    @staticmethod
    async def get_booking(booking_id: str) -> ViewingBooking:
        with db.get_session() as session:
            rec = session.run(
                "MATCH (b:ViewingBooking {id: $id}) RETURN b", id=booking_id
            ).single()
            if not rec:
                raise HTTPException(status_code=404, detail="Booking not found.")
            bd = rec["b"]
            starts_at = bd.get("starts_at")
            return ViewingBooking(
                id=bd["id"],
                starts_at=_native(starts_at).isoformat() if starts_at else None,
                name=bd["name"],
                email=bd["email"],
                phone=bd.get("phone"),
                status=bd["status"],
                created_at=_native(bd["created_at"]).isoformat(),
                address_sent=bool(bd.get("address_sent_at")),
            )

    @staticmethod
    async def mark_address_sent(booking_id: str) -> None:
        with db.get_session() as session:
            session.run(
                "MATCH (b:ViewingBooking {id: $id}) SET b.address_sent_at = datetime()",
                id=booking_id,
            )

    @staticmethod
    async def cancel_by_token(token: str) -> ViewingBooking:
        with db.get_session() as session:
            rec = session.run(
                "MATCH (b:ViewingBooking {cancel_token: $t}) RETURN b", t=token
            ).single()
            if not rec:
                raise HTTPException(status_code=404, detail="Booking not found.")
            bd = rec["b"]
            if bd["status"] != "cancelled":
                session.run(
                    "MATCH (b:ViewingBooking {cancel_token: $t}) "
                    "SET b.status = 'cancelled', b.cancelled_at = datetime()",
                    t=token,
                )
            starts_at = bd.get("starts_at")
            return ViewingBooking(
                id=bd["id"],
                starts_at=_native(starts_at).isoformat() if starts_at else None,
                name=bd["name"],
                email=bd["email"],
                phone=bd.get("phone"),
                status="cancelled",
                created_at=_native(bd["created_at"]).isoformat(),
            )
