from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas.curated_source import CuratedSourceCreate, CuratedSourceResponse

router = APIRouter(prefix="/curated-sources", tags=["curated-sources"])


@router.get("/", response_model=List[CuratedSourceResponse])
def list_curated_sources(db: Session = Depends(get_db)):
    return db.query(models.CuratedSource).all()


@router.post("/", response_model=CuratedSourceResponse)
def create_curated_source(source: CuratedSourceCreate, db: Session = Depends(get_db)):
    db_source = models.CuratedSource(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.delete("/{source_id}")
def delete_curated_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.CuratedSource).filter(
        models.CuratedSource.id == source_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Curated source not found")
    db.delete(source)
    db.commit()
    return {"detail": "Curated source deleted"}