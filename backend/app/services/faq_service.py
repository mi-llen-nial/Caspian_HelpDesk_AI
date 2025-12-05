from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.faq import FAQ
from app.schemas.faq import FAQCreate, FAQUpdate


def create_faq(db: Session, data: FAQCreate) -> FAQ:
    faq = FAQ(
        question=data.question,
        answer=data.answer,
        language=data.language,
        category_code=data.category_code,
        auto_resolvable=data.auto_resolvable,
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


def list_faq(db: Session, language: Optional[str] = None) -> List[FAQ]:
    query = db.query(FAQ)
    if language:
        query = query.filter(FAQ.language == language)
    return query.order_by(FAQ.id.desc()).all()


def update_faq(db: Session, faq_id: int, data: FAQUpdate) -> FAQ:
    faq: FAQ | None = db.query(FAQ).get(faq_id)
    if not faq:
        raise ValueError("FAQ not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(faq, field, value)
    db.commit()
    db.refresh(faq)
    return faq


def delete_faq(db: Session, faq_id: int) -> None:
    faq: FAQ | None = db.query(FAQ).get(faq_id)
    if not faq:
        raise ValueError("FAQ not found")
    db.delete(faq)
    db.commit()


def get_best_match(db: Session, category_code: str | None, language: str) -> Optional[FAQ]:
    """Простейший поиск статьи по категории и языку."""
    query = db.query(FAQ).filter(FAQ.language == language, FAQ.auto_resolvable.is_(True))
    if category_code:
        query = query.filter(FAQ.category_code == category_code)
    return query.first()
