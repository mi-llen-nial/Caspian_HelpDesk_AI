from sqlalchemy.orm import Session

from app.db.session import get_db as _get_db


def get_db() -> Session:
    yield from _get_db()

