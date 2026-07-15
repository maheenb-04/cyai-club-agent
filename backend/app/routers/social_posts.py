from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.social_post import SocialPostResponse, SocialPostUpdate
from app.services.social_generator import generate_circlein_post, generate_instagram_post
from app.core.limiter import limiter

router = APIRouter(prefix="/social-posts", tags=["social-posts"])


@router.get("/", response_model=List[SocialPostResponse])
def list_social_posts(platform: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.SocialPost)
    if platform:
        query = query.filter(models.SocialPost.platform == platform)
    return query.order_by(models.SocialPost.created_at.desc()).all()


@router.post("/generate", response_model=SocialPostResponse)
@limiter.limit("20/hour")
def generate_social_post(
    request: Request,
    platform: str,
    opportunity_id: Optional[int] = None,
    event_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if platform not in ("circlein", "instagram"):
        raise HTTPException(status_code=400, detail="platform must be 'circlein' or 'instagram'")

    if not opportunity_id and not event_id:
        raise HTTPException(status_code=400, detail="Must provide either opportunity_id or event_id")

    opportunity = None
    event = None

    if opportunity_id:
        opportunity = db.query(models.Opportunity).filter(
            models.Opportunity.id == opportunity_id
        ).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    if event_id:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    if platform == "circlein":
        result = generate_circlein_post(opportunity, event)
        db_post = models.SocialPost(
            opportunity_id=opportunity_id,
            platform="circlein",
            content=result.get("content", ""),
            status="draft",
            posting_mode="manual",
        )
    else:
        result = generate_instagram_post(opportunity, event)
        db_post = models.SocialPost(
            opportunity_id=opportunity_id,
            platform="instagram",
            caption=result.get("caption", ""),
            hashtags=result.get("hashtags", ""),
            status="draft",
            posting_mode="manual",
        )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.patch("/{post_id}", response_model=SocialPostResponse)
def update_social_post(post_id: int, update: SocialPostUpdate, db: Session = Depends(get_db)):
    post = db.query(models.SocialPost).filter(models.SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Social post not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}")
def delete_social_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.SocialPost).filter(models.SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Social post not found")
    db.delete(post)
    db.commit()
    return {"detail": "Social post deleted"}
