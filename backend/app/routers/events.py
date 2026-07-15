from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.event import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=List[EventResponse])
def list_events(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.Event)
    if active_only:
        query = query.filter(models.Event.is_active == True)
    return query.order_by(models.Event.created_at.desc()).all()


@router.post("/", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"detail": "Event deleted"}
