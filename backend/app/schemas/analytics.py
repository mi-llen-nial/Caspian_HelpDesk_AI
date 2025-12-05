from datetime import datetime

from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    total_tickets: int
    new_today: int
    auto_closed_percent: float
    avg_first_response_minutes: float | None
    classification_accuracy: float | None
    generated_at: datetime

