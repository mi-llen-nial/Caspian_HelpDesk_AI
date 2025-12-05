from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuthorType(str, Enum):
    CUSTOMER = "customer"
    AGENT = "agent"
    AI = "ai"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)

    author_type = Column(String(20), nullable=False, default=AuthorType.CUSTOMER.value)
    body = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")
