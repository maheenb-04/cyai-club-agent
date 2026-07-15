from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventBase(BaseModel):
    title: str
    event_date: Optional[str] = None
    time_display: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    rsvp_link: Optional[str] = None
    event_type: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
