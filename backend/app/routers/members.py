from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.member import MemberCreate, MemberResponse
from app.services.tokens import verify_unsubscribe_token
from app.core.security import verify_api_key

router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=List[MemberResponse], dependencies=[Depends(verify_api_key)])
def list_members(active_only: bool = True, db: Session = Depends(get_db)):
    query = db.query(models.Member)
    if active_only:
        query = query.filter(models.Member.is_active == True)
    return query.all()


@router.post("/", response_model=MemberResponse, dependencies=[Depends(verify_api_key)])
def add_member(member: MemberCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Member).filter(models.Member.email == member.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member with this email already exists")

    db_member = models.Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.post("/bulk-import", dependencies=[Depends(verify_api_key)])
def bulk_import_members(emails: List[str], db: Session = Depends(get_db)):
    added = 0
    skipped = 0

    for email in emails:
        email = email.strip()
        if not email:
            continue

        existing = db.query(models.Member).filter(models.Member.email == email).first()
        if existing:
            skipped += 1
            continue

        db.add(models.Member(email=email, is_active=True))
        added += 1

    db.commit()
    return {"added": added, "skipped_duplicates": skipped}


@router.get("/unsubscribe")
def unsubscribe(token: str, db: Session = Depends(get_db)):
    try:
        email = verify_unsubscribe_token(token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired unsubscribe link")

    member = db.query(models.Member).filter(models.Member.email == email).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_active = False
    db.commit()
    return {"detail": f"{email} has been unsubscribed successfully"}


@router.delete("/{member_id}", dependencies=[Depends(verify_api_key)])
def remove_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return {"detail": "Member removed"}
