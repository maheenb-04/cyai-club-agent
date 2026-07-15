from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NewsletterResponse(BaseModel):
    id: int
    created_at: datetime
    status: str
    subject: Optional[str] = None
    html_content: Optional[str] = None
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsletterUpdate(BaseModel):
    subject: Optional[str] = None
    html_content: Optional[str] = None
    status: Optional[str] = None