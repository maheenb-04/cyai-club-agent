from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MemberBase(BaseModel):
    email: str
    name: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class MemberResponse(MemberBase):
    id: int
    is_active: bool
    added_at: datetime

    class Config:
        from_attributes = True
