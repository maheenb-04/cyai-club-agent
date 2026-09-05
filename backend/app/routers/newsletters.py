import re
import os
import uuid
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.newsletter import NewsletterResponse, NewsletterUpdate
from app.services.newsletter_generator import generate_newsletter_html
from app.services.email_sender import send_newsletter_to_members
from app.services.newsletter_renderer import render_newsletter_pdf
from app.core.limiter import limiter

router = APIRouter(prefix="/newsletters", tags=["newsletters"])

ATTACHMENT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "newsletter_attachments")
ALLOWED_ATTACHMENT_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg")


class TestSendRequest(BaseModel):
    test_email: str


def _extract_intro_html(html_content: str) -> str:
    match = re.search(r"^(.*?)(?=<h2)", html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return html_content[:500]


def _get_attachment_filenames(newsletter) -> list:
    if not newsletter.attachment_filenames:
        return []
    return [f for f in newsletter.attachment_filenames.split(",") if f]


def _get_attachment_paths(newsletter) -> list:
    return [os.path.join(ATTACHMENT_DIR, f) for f in _get_attachment_filenames(newsletter)]


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

    last_newsletter = db.query(models.Newsletter).order_by(
        models.Newsletter.created_at.desc()
    ).first()

    recently_featured_ids = set()
    if last_newsletter:
        links = db.query(models.NewsletterOpportunity).filter(
            models.NewsletterOpportunity.newsletter_id == last_newsletter.id
        ).all()
        recently_featured_ids = {link.opportunity_id for link in links}

    result = generate_newsletter_html(opportunities, month_label, events, recently_featured_ids)

    newsletter = models.Newsletter(
        status="draft",
        subject=result.get("subject", f"CYAI {month_label} Newsletter"),
        html_content=result.get("html_content", ""),
    )
    db.add(newsletter)
    db.commit()
    db.refresh(newsletter)

    included_ids = result.get("included_opportunity_ids", [])
    for opp_id in included_ids:
        db.add(models.NewsletterOpportunity(newsletter_id=newsletter.id, opportunity_id=opp_id))
    db.commit()

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


@router.get("/{newsletter_id}/opportunities")
def get_newsletter_opportunities(newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    links = db.query(models.NewsletterOpportunity).filter(
        models.NewsletterOpportunity.newsletter_id == newsletter_id
    ).all()

    opportunity_ids = [link.opportunity_id for link in links]
    opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.id.in_(opportunity_ids)
    ).all()

    return [{"id": o.id, "title": o.title, "category": o.category} for o in opportunities]


@router.get("/{newsletter_id}/render-pdf")
@limiter.limit("10/hour")
def render_newsletter_as_pdf(request: Request, newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    links = db.query(models.NewsletterOpportunity).filter(
        models.NewsletterOpportunity.newsletter_id == newsletter_id
    ).all()
    opportunity_ids = [link.opportunity_id for link in links]
    opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.id.in_(opportunity_ids)
    ).all()

    opportunities_by_category = {}
    for opp in opportunities:
        opportunities_by_category.setdefault(opp.category, []).append({
            "title": opp.title,
            "organization": opp.organization,
            "deadline": opp.deadline,
            "url": opp.url,
            "eligibility": opp.eligibility,
            "description": opp.description,
            "category": opp.category,
        })

    events = db.query(models.Event).filter(models.Event.is_active == True).all()
    events_data = [{
        "title": ev.title,
        "event_date": ev.event_date,
        "time_display": ev.time_display,
        "location": ev.location,
        "description": ev.description,
        "rsvp_link": ev.rsvp_link,
        "image_filename": ev.image_filename,
    } for ev in events]

    intro_html = _extract_intro_html(newsletter.html_content or "")

    pdf_bytes = render_newsletter_pdf(newsletter.subject, intro_html, events_data, opportunities_by_category)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cyai_newsletter_{newsletter_id}.pdf"},
    )


@router.get("/{newsletter_id}/attachments")
def list_attachments(newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return {"filenames": _get_attachment_filenames(newsletter)}


@router.post("/{newsletter_id}/attachments")
def upload_attachment(newsletter_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF, PNG, and JPG files are allowed")

    os.makedirs(ATTACHMENT_DIR, exist_ok=True)
    stored_filename = f"{newsletter_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    filepath = os.path.join(ATTACHMENT_DIR, stored_filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    existing = _get_attachment_filenames(newsletter)
    existing.append(stored_filename)
    newsletter.attachment_filenames = ",".join(existing)
    db.commit()

    return {"filenames": existing}


@router.delete("/{newsletter_id}/attachments/{stored_filename}")
def delete_attachment(newsletter_id: int, stored_filename: str, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    existing = _get_attachment_filenames(newsletter)
    if stored_filename in existing:
        existing.remove(stored_filename)
        newsletter.attachment_filenames = ",".join(existing)
        db.commit()

        filepath = os.path.join(ATTACHMENT_DIR, stored_filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    return {"filenames": existing}


@router.post("/{newsletter_id}/send-test")
@limiter.limit("10/hour")
def send_test_newsletter(request: Request, newsletter_id: int, body: TestSendRequest, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    attachment_paths = _get_attachment_paths(newsletter)

    result = send_newsletter_to_members(
        [body.test_email],
        f"[TEST] {newsletter.subject}",
        newsletter.html_content,
        attachment_paths,
    )

    return {
        "newsletter_id": newsletter_id,
        "test_email": body.test_email,
        "sent": result["sent"],
        "failed": result["failed"],
    }


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
    attachment_paths = _get_attachment_paths(newsletter)

    result = send_newsletter_to_members(
        member_emails,
        newsletter.subject,
        newsletter.html_content,
        attachment_paths,
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
