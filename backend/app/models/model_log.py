from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.db.base import Base


class ModelLog(Base):
    __tablename__ = "model_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True, index=True)

    model_name = Column(String(100), nullable=False)
    input_type = Column(String(50), nullable=False)  # classification / summary / answer
    request_payload = Column(Text, nullable=False)
    response_payload = Column(Text, nullable=False)

    confidence = Column(Float, nullable=True)
    was_corrected = Column(Integer, default=0)  # 0 / 1

    created_at = Column(DateTime, default=datetime.utcnow)

