from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..models import Event, EventCreate, EventUpdate, User
from ..crud.events import EventCRUD
from app.core.security import get_current_user

router = APIRouter()


@router.post("/events/", response_model=Event, status_code=status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new event. Requires authentication.
    The authenticated user will be set as the event creator.
    """
    try:
        return await EventCRUD.create(event, creator_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(ex)}",
        )


@router.get("/events/", response_model=List[Event])
async def get_events():
    """
    Retrieve the list of all events.
    """
    events = await EventCRUD.get_all()
    if not events:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found.")
    return events


@router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    """
    Retrieve a specific event by ID.
    """
    event = await EventCRUD.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return event


@router.put("/events/{event_id}", response_model=Event)
async def update_event(
    event_id: str,
    event: EventUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update event details by event ID. Requires authentication.
    """
    # Check if event exists and user is the creator
    existing_event = await EventCRUD.get_by_id(event_id)
    if not existing_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    if existing_event.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this event."
        )

    updated_event = await EventCRUD.update(event_id, event)
    if not updated_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    return updated_event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an event by ID. Requires authentication.
    Only the event creator can delete the event.
    """
    # Check if event exists and user is the creator
    existing_event = await EventCRUD.get_by_id(event_id)
    if not existing_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    if existing_event.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this event."
        )

    success = await EventCRUD.delete(event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")