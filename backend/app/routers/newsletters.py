from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.newsletter import NewsletterResponse, NewsletterUpdate
from app.services.newsletter_generator import generate_newsletter_html

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
def generate_newsletter(month_label: str, db: Session = Depends(get_db)):
    opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    if not opportunities:
        raise HTTPException(status_code=400, detail="No active opportunities to include")

    result = generate_newsletter_html(opportunities, month_label)

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


@router.delete("/{newsletter_id}")
def delete_newsletter(newsletter_id: int, db: Session = Depends(get_db)):
    newsletter = db.query(models.Newsletter).filter(models.Newsletter.id == newsletter_id).first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    db.delete(newsletter)
    db.commit()
    return {"detail": "Newsletter deleted"}