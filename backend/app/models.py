from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    organization = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    deadline = Column(String, nullable=True)
    eligibility = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    source_type = Column(String, nullable=False, default="curated")
    date_added = Column(DateTime, default=datetime.utcnow)
    last_validated_at = Column(DateTime, nullable=True)
    link_status = Column(String, default="unchecked")
    is_active = Column(Boolean, default=True)


class CuratedSource(Base):
    __tablename__ = "curated_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    category = Column(String, nullable=False)
    check_frequency = Column(String, default="weekly")
    last_checked_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    unsubscribe_token = Column(String, nullable=True, unique=True)


class Newsletter(Base):
    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="draft")
    subject = Column(String, nullable=True)
    html_content = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    opportunities = relationship(
        "NewsletterOpportunity", back_populates="newsletter"
    )


class NewsletterOpportunity(Base):
    __tablename__ = "newsletter_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    newsletter_id = Column(Integer, ForeignKey("newsletters.id"))
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))

    newsletter = relationship("Newsletter", back_populates="opportunities")


class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    platform = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    status = Column(String, default="draft")
    posting_mode = Column(String, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    external_post_id = Column(String, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    event_date = Column(String, nullable=True)
    time_display = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    rsvp_link = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    image_filename = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
