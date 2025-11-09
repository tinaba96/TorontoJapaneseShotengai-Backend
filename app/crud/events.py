from app.crud.database import db
from typing import Optional, List
from fastapi import HTTPException, status
from app.models import Event, EventCreate, EventUpdate
from uuid import uuid4


class EventCRUD:
    @staticmethod
    async def create(event: EventCreate, creator_id: str) -> Event:
        """
        Create a new event and link it to the creator user.
        """
        with db.get_session() as session:
            # Generate event ID
            event_id = str(uuid4())

            # Create event in database
            create_result = session.run(
                """
                CREATE (e:Event {
                    id: $id,
                    title: $title,
                    description: $description,
                    contactEmail: $contactEmail,
                    contactPhone: $contactPhone,
                    eventDate: $eventDate,
                    eventTime: $eventTime,
                    venue: $venue,
                    organizer: $organizer,
                    maxAttendees: $maxAttendees,
                    creator_id: $creator_id,
                    current_attendees: 0,
                    status: 'upcoming',
                    created_at: datetime(),
                    updated_at: datetime()
                })
                RETURN e
                """,
                id=event_id,
                title=event.title,
                description=event.description,
                contactEmail=event.contactEmail,
                contactPhone=event.contactPhone,
                eventDate=event.eventDate,
                eventTime=event.eventTime,
                venue=event.venue,
                organizer=event.organizer,
                maxAttendees=event.maxAttendees,
                creator_id=creator_id,
            )
            record = create_result.single()
            if not record:
                raise HTTPException(status_code=500, detail="Failed to create event.")

            # Create relationship between user and event
            session.run(
                """
                MATCH (u:User {id: $user_id}), (e:Event {id: $event_id})
                CREATE (u)-[:CREATED]->(e)
                """,
                user_id=creator_id,
                event_id=event_id,
            )

            # Return created event
            event_data = record["e"]
            return Event(
                id=event_data["id"],
                title=event_data["title"],
                description=event_data["description"],
                contactEmail=event_data["contactEmail"],
                contactPhone=event_data.get("contactPhone"),
                eventDate=event_data["eventDate"],
                eventTime=event_data["eventTime"],
                venue=event_data["venue"],
                organizer=event_data["organizer"],
                maxAttendees=event_data.get("maxAttendees"),
                creator_id=event_data["creator_id"],
                current_attendees=event_data["current_attendees"],
                status=event_data["status"],
                created_at=event_data["created_at"].isoformat(),
                updated_at=event_data["updated_at"].isoformat() if event_data.get("updated_at") else None,
            )

    @staticmethod
    async def get_all() -> List[Event]:
        """
        Retrieve all events from the database.
        """
        with db.get_session() as session:
            result = session.run("MATCH (e:Event) RETURN e ORDER BY e.created_at DESC")
            events = []
            for record in result:
                event_data = record["e"]
                events.append(
                    Event(
                        id=event_data["id"],
                        title=event_data["title"],
                        description=event_data["description"],
                        contactEmail=event_data["contactEmail"],
                        contactPhone=event_data.get("contactPhone"),
                        eventDate=event_data["eventDate"],
                        eventTime=event_data["eventTime"],
                        venue=event_data["venue"],
                        organizer=event_data["organizer"],
                        maxAttendees=event_data.get("maxAttendees"),
                        creator_id=event_data["creator_id"],
                        current_attendees=event_data["current_attendees"],
                        status=event_data["status"],
                        created_at=event_data["created_at"].isoformat(),
                        updated_at=event_data["updated_at"].isoformat() if event_data.get("updated_at") else None,
                    )
                )
            return events

    @staticmethod
    async def get_by_id(event_id: str) -> Optional[Event]:
        """
        Retrieve an event by its ID.
        """
        with db.get_session() as session:
            result = session.run(
                "MATCH (e:Event {id: $id}) RETURN e", id=event_id
            )
            record = result.single()
            if record:
                event_data = record["e"]
                return Event(
                    id=event_data["id"],
                    title=event_data["title"],
                    description=event_data["description"],
                    contactEmail=event_data["contactEmail"],
                    contactPhone=event_data.get("contactPhone"),
                    eventDate=event_data["eventDate"],
                    eventTime=event_data["eventTime"],
                    venue=event_data["venue"],
                    organizer=event_data["organizer"],
                    maxAttendees=event_data.get("maxAttendees"),
                    creator_id=event_data["creator_id"],
                    current_attendees=event_data["current_attendees"],
                    status=event_data["status"],
                    created_at=event_data["created_at"].isoformat(),
                    updated_at=event_data["updated_at"].isoformat() if event_data.get("updated_at") else None,
                )
            return None

    @staticmethod
    async def update(event_id: str, event: EventUpdate) -> Optional[Event]:
        """
        Update event details by ID.
        """
        with db.get_session() as session:
            # Build update query dynamically based on provided fields
            update_fields = []
            params = {"id": event_id}

            if event.title is not None:
                update_fields.append("e.title = $title")
                params["title"] = event.title
            if event.description is not None:
                update_fields.append("e.description = $description")
                params["description"] = event.description
            if event.contactEmail is not None:
                update_fields.append("e.contactEmail = $contactEmail")
                params["contactEmail"] = event.contactEmail
            if event.contactPhone is not None:
                update_fields.append("e.contactPhone = $contactPhone")
                params["contactPhone"] = event.contactPhone
            if event.eventDate is not None:
                update_fields.append("e.eventDate = $eventDate")
                params["eventDate"] = event.eventDate
            if event.eventTime is not None:
                update_fields.append("e.eventTime = $eventTime")
                params["eventTime"] = event.eventTime
            if event.venue is not None:
                update_fields.append("e.venue = $venue")
                params["venue"] = event.venue
            if event.organizer is not None:
                update_fields.append("e.organizer = $organizer")
                params["organizer"] = event.organizer
            if event.maxAttendees is not None:
                update_fields.append("e.maxAttendees = $maxAttendees")
                params["maxAttendees"] = event.maxAttendees
            if event.status is not None:
                update_fields.append("e.status = $status")
                params["status"] = event.status

            if not update_fields:
                # No fields to update
                return await EventCRUD.get_by_id(event_id)

            update_fields.append("e.updated_at = datetime()")
            update_query = f"""
                MATCH (e:Event {{id: $id}})
                SET {', '.join(update_fields)}
                RETURN e
            """

            result = session.run(update_query, **params)
            record = result.single()

            if record:
                event_data = record["e"]
                return Event(
                    id=event_data["id"],
                    title=event_data["title"],
                    description=event_data["description"],
                    contactEmail=event_data["contactEmail"],
                    contactPhone=event_data.get("contactPhone"),
                    eventDate=event_data["eventDate"],
                    eventTime=event_data["eventTime"],
                    venue=event_data["venue"],
                    organizer=event_data["organizer"],
                    maxAttendees=event_data.get("maxAttendees"),
                    creator_id=event_data["creator_id"],
                    current_attendees=event_data["current_attendees"],
                    status=event_data["status"],
                    created_at=event_data["created_at"].isoformat(),
                    updated_at=event_data["updated_at"].isoformat() if event_data.get("updated_at") else None,
                )
            return None

    @staticmethod
    async def delete(event_id: str) -> bool:
        """
        Delete an event by ID.
        """
        with db.get_session() as session:
            result = session.run(
                """
                MATCH (e:Event {id: $id})
                DETACH DELETE e
                """,
                id=event_id
            )
            return bool(result.summary().counters.nodes_deleted)