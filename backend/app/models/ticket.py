from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class TicketStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    AUTO_CLOSED = "auto_closed"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, default="portal")  # telegram / email / portal / phone
    language = Column(String(10), nullable=False, default="ru")

    customer_email = Column(String(255), nullable=True, index=True)
    customer_username = Column(String(255), nullable=True, index=True)
    external_user_id = Column(String(100), nullable=True)  # например, Telegram user id или message id
    request_type = Column(
        String(50),
        nullable=True,
    )  # problem / question / feedback / career / partner / other (также возможны старые значения difficulty / proposal / job)

    category_code = Column(String(100), nullable=True, index=True)
    priority = Column(String(10), nullable=False, default="P3")

    status = Column(String(50), nullable=False, default=TicketStatus.NEW.value)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    auto_closed_by_ai = Column(Boolean, default=False)
    ai_disabled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status_updated_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    department = relationship("Department")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan")
