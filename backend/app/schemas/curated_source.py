from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CuratedSourceBase(BaseModel):
    name: str
    url: str
    category: str
    check_frequency: str = "weekly"
    notes: Optional[str] = None


class CuratedSourceCreate(CuratedSourceBase):
    pass


class CuratedSourceResponse(CuratedSourceBase):
    id: int
    last_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True
