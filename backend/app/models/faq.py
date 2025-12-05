from sqlalchemy import Boolean, Column, Integer, String, Text

from app.db.base import Base


class FAQ(Base):
    __tablename__ = "faq"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(255), nullable=False)
    answer = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default="ru")
    category_code = Column(String(100), nullable=True, index=True)
    auto_resolvable = Column(Boolean, default=False)

