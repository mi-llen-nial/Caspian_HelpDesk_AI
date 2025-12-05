from datetime import datetime

from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    total_tickets: int
    new_today: int
    in_progress_tickets: int
    closed_today: int
    auto_closed_percent: float
    user_auto_closed_tickets: int
    avg_first_response_minutes: float | None
    classification_accuracy: float | None
    # По категориям (request_type)
    problem_tickets: int
    question_tickets: int
    feedback_tickets: int
    career_tickets: int
    partner_tickets: int
    other_tickets: int
    # По приоритетам
    p1_tickets: int
    p2_tickets: int
    p3_tickets: int
    p4_tickets: int
    generated_at: datetime
