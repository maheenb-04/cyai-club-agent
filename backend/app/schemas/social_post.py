from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SocialPostResponse(BaseModel):
    id: int
    opportunity_id: Optional[int] = None
    platform: str
    content: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    status: str
    posting_mode: str
    created_at: datetime
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SocialPostUpdate(BaseModel):
    content: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    status: Optional[str] = None
