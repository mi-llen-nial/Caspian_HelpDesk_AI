from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.faq import FAQCreate, FAQRead, FAQUpdate
from app.services import faq_service

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("", response_model=List[FAQRead])
def list_faq(
    db: Session = Depends(get_db),
    language: Optional[str] = Query(None),
):
    items = faq_service.list_faq(db, language=language)
    return [FAQRead.model_validate(f) for f in items]


@router.post("", response_model=FAQRead)
def create_faq(data: FAQCreate, db: Session = Depends(get_db)):
    faq = faq_service.create_faq(db, data)
    return FAQRead.model_validate(faq)


@router.put("/{faq_id}", response_model=FAQRead)
def update_faq(faq_id: int, data: FAQUpdate, db: Session = Depends(get_db)):
    try:
        faq = faq_service.update_faq(db, faq_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return FAQRead.model_validate(faq)


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    try:
        faq_service.delete_faq(db, faq_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="FAQ not found")
