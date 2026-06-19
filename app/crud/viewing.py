from app.crud.database import db
from fastapi import HTTPException, status
from app.models.viewing import (
    ViewingSlot,
    ViewingSlotCreate,
    ViewingBooking,
    ViewingBookingCreate,
)
from typing import List, Tuple
from uuid import uuid4


class ViewingCRUD:
    # ----- Slots -----------------------------------------------------------
    @staticmethod
    async def create_slot(slot: ViewingSlotCreate) -> ViewingSlot:
        with db.get_session() as session:
            slot_id = str(uuid4())
            result = session.run(
                """
                CREATE (s:ViewingSlot {
                    id: $id,
                    starts_at: datetime($starts_at),
                    created_at: datetime()
                })
                RETURN s
                """,
                id=slot_id,
                starts_at=slot.starts_at,
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create slot.")
            s = record["s"]
            return ViewingSlot(
                id=s["id"],
                starts_at=s["starts_at"].isoformat(),
                booking_count=0,
                created_at=s["created_at"].isoformat(),
            )

    @staticmethod
    async def get_slots(upcoming_only: bool = True) -> List[ViewingSlot]:
        with db.get_session() as session:
            where_clause = "WHERE s.starts_at >= datetime()" if upcoming_only else ""
            result = session.run(
                f"""
                MATCH (s:ViewingSlot)
                {where_clause}
                OPTIONAL MATCH (s)-[:HAS_BOOKING]->(b:ViewingBooking {{status: 'active'}})
                RETURN s, count(b) AS booking_count
                ORDER BY s.starts_at ASC
                """
            )
            slots = []
            for record in result:
                s = record["s"]
                slots.append(
                    ViewingSlot(
                        id=s["id"],
                        starts_at=s["starts_at"].isoformat(),
                        booking_count=record["booking_count"],
                        created_at=s["created_at"].isoformat(),
                    )
                )
            return slots

    @staticmethod
    async def delete_slot(slot_id: str) -> bool:
        """
        Delete a slot. Refuses (409) if the slot still has active bookings,
        per spec ("予約が入っている枠は削除不可").
        Returns False if the slot did not exist.
        """
        with db.get_session() as session:
            check = session.run(
                """
                MATCH (s:ViewingSlot {id: $id})-[:HAS_BOOKING]->(b:ViewingBooking {status: 'active'})
                RETURN count(b) AS c
                """,
                id=slot_id,
            )
            rec = check.single()
            if rec and rec["c"] > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot delete a slot that has active bookings.",
                )
            result = session.run(
                "MATCH (s:ViewingSlot {id: $id}) DETACH DELETE s",
                id=slot_id,
            )
            summary = result.consume()
            return summary.counters.nodes_deleted > 0

    # ----- Bookings --------------------------------------------------------
    @staticmethod
    async def create_booking(b: ViewingBookingCreate) -> Tuple[ViewingBooking, str]:
        """
        Create a booking for a slot. Returns (booking, cancel_token).
        Rules:
          - slot must exist
          - one ACTIVE booking per email (複数予約不可)
          - a slot can hold unlimited people (人数無制限)
        """
        with db.get_session() as session:
            slot_res = session.run(
                "MATCH (s:ViewingSlot {id: $sid}) RETURN s",
                sid=b.slot_id,
            )
            if not slot_res.single():
                raise HTTPException(status_code=404, detail="Slot not found.")

            existing = session.run(
                "MATCH (b:ViewingBooking {email: $email, status: 'active'}) RETURN b LIMIT 1",
                email=b.email,
            )
            if existing.single():
                raise HTTPException(
                    status_code=400,
                    detail="You already have an active booking. Please cancel it before booking another time.",
                )

            booking_id = str(uuid4())
            cancel_token = str(uuid4())
            result = session.run(
                """
                MATCH (s:ViewingSlot {id: $sid})
                CREATE (bk:ViewingBooking {
                    id: $id,
                    slot_id: $sid,
                    name: $name,
                    email: $email,
                    phone: $phone,
                    status: 'active',
                    cancel_token: $token,
                    created_at: datetime()
                })
                CREATE (s)-[:HAS_BOOKING]->(bk)
                RETURN bk, s.starts_at AS starts_at
                """,
                sid=b.slot_id,
                id=booking_id,
                name=b.name,
                email=b.email,
                phone=b.phone,
                token=cancel_token,
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create booking.")
            bd = record["bk"]
            booking = ViewingBooking(
                id=bd["id"],
                slot_id=bd["slot_id"],
                starts_at=record["starts_at"].isoformat() if record["starts_at"] else None,
                name=bd["name"],
                email=bd["email"],
                phone=bd.get("phone"),
                status=bd["status"],
                created_at=bd["created_at"].isoformat(),
            )
            return booking, cancel_token

    @staticmethod
    async def get_bookings() -> List[ViewingBooking]:
        with db.get_session() as session:
            result = session.run(
                """
                MATCH (bk:ViewingBooking)
                OPTIONAL MATCH (s:ViewingSlot)-[:HAS_BOOKING]->(bk)
                RETURN bk, s.starts_at AS starts_at
                ORDER BY starts_at ASC, bk.created_at ASC
                """
            )
            bookings = []
            for record in result:
                bd = record["bk"]
                starts_at = record["starts_at"]
                bookings.append(
                    ViewingBooking(
                        id=bd["id"],
                        slot_id=bd["slot_id"],
                        starts_at=starts_at.isoformat() if starts_at else None,
                        name=bd["name"],
                        email=bd["email"],
                        phone=bd.get("phone"),
                        status=bd["status"],
                        created_at=bd["created_at"].isoformat(),
                    )
                )
            return bookings

    @staticmethod
    async def cancel_by_token(token: str) -> ViewingBooking:
        with db.get_session() as session:
            result = session.run(
                """
                MATCH (bk:ViewingBooking {cancel_token: $token})
                OPTIONAL MATCH (s:ViewingSlot)-[:HAS_BOOKING]->(bk)
                RETURN bk, s.starts_at AS starts_at
                """,
                token=token,
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Booking not found.")
            bd = record["bk"]
            starts_at = record["starts_at"]

            if bd["status"] != "cancelled":
                session.run(
                    """
                    MATCH (bk:ViewingBooking {cancel_token: $token})
                    SET bk.status = 'cancelled', bk.cancelled_at = datetime()
                    """,
                    token=token,
                )

            return ViewingBooking(
                id=bd["id"],
                slot_id=bd["slot_id"],
                starts_at=starts_at.isoformat() if starts_at else None,
                name=bd["name"],
                email=bd["email"],
                phone=bd.get("phone"),
                status="cancelled",
                created_at=bd["created_at"].isoformat(),
            )
