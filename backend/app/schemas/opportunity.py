from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OpportunityBase(BaseModel):
    category: str
    title: str
    organization: Optional[str] = None
    description: Optional[str] = None
    url: str
    deadline: Optional[str] = None
    eligibility: Optional[str] = None
    source: Optional[str] = None
    source_type: str = "curated"


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityResponse(OpportunityBase):
    id: int
    date_added: datetime
    last_validated_at: Optional[datetime] = None
    link_status: str
    is_active: bool

    class Config:
        from_attributes = True