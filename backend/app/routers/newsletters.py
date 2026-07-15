from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.newsletter import NewsletterResponse, NewsletterUpdate
from app.services.newsletter_generator import generate_newsletter_html
from app.services.email_sender import send_newsletter_to_members
from app.core.limiter import limiter

router = APIRouter(prefix="/newsletters", tags=["newsletters"])


@router.get("/", response_model=List[NewsletterResponse])
def list_newsletters(db: Session = Depends(get_db)):
    return db.query(models.Newsletter).order_by(models.Newsletter.created_at.desc()).all()


@router.get("/{newsletter_id}", response_model=NewsletterResponse)
def get_newsletter(newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return newsletter


@router.post("/generate", response_model=NewsletterResponse)
@limiter.limit("10/hour")
def generate_newsletter(request: Request, month_label: str, db: Session = Depends(get_db)):
    opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    events = db.query(models.Event).filter(models.Event.is_active == True).all()

    if not opportunities and not events:
        raise HTTPException(status_code=400, detail="No active opportunities or events to include")

    result = generate_newsletter_html(opportunities, month_label, events)

    newsletter = models.Newsletter(
        status="draft",
        subject=result.get("subject", f"CYAI {month_label} Newsletter"),
        html_content=result.get("html_content", ""),
    )
    db.add(newsletter)
    db.commit()
    db.refresh(newsletter)
    return newsletter


@router.patch("/{newsletter_id}", response_model=NewsletterResponse)
def update_newsletter(newsletter_id: int, update: NewsletterUpdate, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(newsletter, key, value)

    db.commit()
    db.refresh(newsletter)
    return newsletter


@router.post("/{newsletter_id}/send")
@limiter.limit("3/hour")
def send_newsletter(request: Request, newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    if newsletter.status == "sent":
        raise HTTPException(status_code=400, detail="This newsletter has already been sent")

    active_members = db.query(models.Member).filter(models.Member.is_active == True).all()
    if not active_members:
        raise HTTPException(status_code=400, detail="No active members to send to")

    member_emails = [m.email for m in active_members]

    result = send_newsletter_to_members(
        member_emails,
        newsletter.subject,
        newsletter.html_content,
    )

    newsletter.status = "sent"
    newsletter.sent_at = datetime.utcnow()
    db.commit()

    return {
        "newsletter_id": newsletter_id,
        "recipients_attempted": len(member_emails),
        "sent": result["sent"],
        "failed": result["failed"],
    }


@router.delete("/{newsletter_id}")
def delete_newsletter(newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    db.delete(newsletter)
    db.commit()
    return {"detail": "Newsletter deleted"}
