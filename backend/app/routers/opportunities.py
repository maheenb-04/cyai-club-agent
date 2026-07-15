from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.opportunity import OpportunityCreate, OpportunityResponse
from app.services.sourcing.ctftime import fetch_upcoming_ctf_events
from app.services.sourcing.job_aggregator import fetch_adzuna_jobs, fetch_adzuna_internships
from app.services.scholarship_finder import find_scholarships
from app.services.link_validator import is_link_valid
from app.core.limiter import limiter

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("/", response_model=List[OpportunityResponse])
def list_opportunities(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(models.Opportunity)
    if category:
        query = query.filter(models.Opportunity.category == category)
    if active_only:
        query = query.filter(models.Opportunity.is_active == True)
    return query.order_by(models.Opportunity.date_added.desc()).all()


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opportunity = db.query(models.Opportunity).filter(
        models.Opportunity.id == opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@router.post("/", response_model=OpportunityResponse)
def create_opportunity(opportunity: OpportunityCreate, db: Session = Depends(get_db)):
    db_opportunity = models.Opportunity(**opportunity.model_dump())
    db.add(db_opportunity)
    db.commit()
    db.refresh(db_opportunity)
    return db_opportunity


@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opportunity = db.query(models.Opportunity).filter(
        models.Opportunity.id == opportunity_id
    ).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    db.delete(opportunity)
    db.commit()
    return {"detail": "Opportunity deleted"}


@router.post("/sync/ctftime")
@limiter.limit("10/hour")
def sync_ctftime(request: Request, db: Session = Depends(get_db)):
    fetched = fetch_upcoming_ctf_events(limit=20)
    added = 0
    skipped = 0

    for item in fetched:
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == item["source"]
        ).first()
        if exists:
            skipped += 1
            continue

        db_opportunity = models.Opportunity(**item)
        db.add(db_opportunity)
        added += 1

    db.commit()
    return {"added": added, "skipped_duplicates": skipped, "total_fetched": len(fetched)}


@router.post("/sync/adzuna")
@limiter.limit("10/hour")
def sync_adzuna(request: Request, db: Session = Depends(get_db)):
    fetched = fetch_adzuna_jobs(results_per_keyword=10)
    added = 0
    skipped = 0

    for item in fetched:
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == item["source"]
        ).first()
        if exists:
            skipped += 1
            continue

        db_opportunity = models.Opportunity(**item)
        db.add(db_opportunity)
        added += 1

    db.commit()
    return {"added": added, "skipped_duplicates": skipped, "total_fetched": len(fetched)}


@router.post("/sync/adzuna-internships")
@limiter.limit("10/hour")
def sync_adzuna_internships(request: Request, db: Session = Depends(get_db)):
    fetched = fetch_adzuna_internships(results_per_keyword=10)
    added = 0
    skipped = 0

    for item in fetched:
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == item["source"]
        ).first()
        if exists:
            skipped += 1
            continue

        db_opportunity = models.Opportunity(**item)
        db.add(db_opportunity)
        added += 1

    db.commit()
    return {"added": added, "skipped_duplicates": skipped, "total_fetched": len(fetched)}


@router.post("/find-scholarships")
@limiter.limit("5/hour")
def find_and_add_scholarships(request: Request, target_month: str, db: Session = Depends(get_db)):
    results = find_scholarships(target_month)
    added = 0
    skipped = 0

    for item in results:
        source = f"ai_search:{item.get('url', '')}"
        exists = db.query(models.Opportunity).filter(
            models.Opportunity.source == source
        ).first()
        if exists:
            skipped += 1
            continue

        db_opportunity = models.Opportunity(
            category="scholarship",
            title=item.get("title", "Untitled"),
            organization=item.get("organization"),
            description=item.get("description"),
            url=item.get("url", ""),
            deadline=item.get("deadline"),
            eligibility=item.get("eligibility"),
            source=source,
            source_type="ai_search",
        )
        db.add(db_opportunity)
        added += 1

    db.commit()
    return {"added": added, "skipped_duplicates": skipped, "total_found": len(results)}


@router.post("/check-links")
@limiter.limit("3/hour")
def check_links(request: Request, db: Session = Depends(get_db)):
    active_opportunities = db.query(models.Opportunity).filter(
        models.Opportunity.is_active == True
    ).all()

    valid_count = 0
    dead_count = 0

    for opp in active_opportunities:
        is_valid = is_link_valid(opp.url)
        opp.link_status = "valid" if is_valid else "dead"
        opp.last_validated_at = datetime.utcnow()

        if is_valid:
            valid_count += 1
        else:
            dead_count += 1

    db.commit()

    return {
        "total_checked": len(active_opportunities),
        "valid": valid_count,
        "dead": dead_count,
        "note": "Dead links are flagged (link_status='dead') but NOT auto-deactivated - review and remove manually if needed.",
    }
