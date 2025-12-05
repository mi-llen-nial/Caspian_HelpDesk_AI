from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.model_log import ModelLog
from app.models.ticket import Ticket, TicketStatus
from app.schemas.analytics import OverviewMetrics


def get_overview_metrics(db: Session) -> OverviewMetrics:
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
    new_today = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.created_at >= today_start)
        .scalar()
        or 0
    )

    auto_closed_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status == TicketStatus.AUTO_CLOSED.value)
        .scalar()
        or 0
    )
    auto_closed_percent = (auto_closed_count / total_tickets * 100.0) if total_tickets else 0.0

    # Упрощённая метрика: пока нет хранения времени первого ответа, берём время до закрытия авто‑тикетов
    avg_first_response_minutes: float | None = None
    if auto_closed_count:
        total_minutes = (
            db.query(func.sum(func.strftime("%s", Ticket.closed_at) - func.strftime("%s", Ticket.created_at)))
            .filter(Ticket.status == TicketStatus.AUTO_CLOSED.value)
            .scalar()
        )
        if total_minutes:
            avg_first_response_minutes = float(total_minutes) / 60.0 / auto_closed_count

    # Оценка "точности" по признаку was_corrected
    total_classifications = (
        db.query(func.count(ModelLog.id)).filter(ModelLog.input_type == "classification").scalar() or 0
    )
    incorrect = (
        db.query(func.count(ModelLog.id))
        .filter(ModelLog.input_type == "classification", ModelLog.was_corrected == 1)
        .scalar()
        or 0
    )
    classification_accuracy: float | None
    if total_classifications:
        classification_accuracy = (total_classifications - incorrect) / total_classifications * 100.0
    else:
        classification_accuracy = None

    return OverviewMetrics(
        total_tickets=total_tickets,
        new_today=new_today,
        auto_closed_percent=auto_closed_percent,
        avg_first_response_minutes=avg_first_response_minutes,
        classification_accuracy=classification_accuracy,
        generated_at=now,
    )

