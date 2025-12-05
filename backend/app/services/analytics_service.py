from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.model_log import ModelLog
from app.models.ticket import Ticket, TicketStatus
from app.models.message import Message, AuthorType
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
    in_progress_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status == TicketStatus.IN_PROGRESS.value)
        .scalar()
        or 0
    )
    closed_today = (
        db.query(func.count(Ticket.id))
        .filter(
            Ticket.closed_at.isnot(None),
            Ticket.closed_at >= today_start,
            Ticket.status.in_([TicketStatus.CLOSED.value, TicketStatus.AUTO_CLOSED.value]),
        )
        .scalar()
        or 0
    )

    # Кол-во заявок по категориям (request_type)
    problem_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.request_type.in_(["problem", "difficulty"]))
        .scalar()
        or 0
    )
    question_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.request_type == "question")
        .scalar()
        or 0
    )
    feedback_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.request_type.in_(["feedback", "proposal"]))
        .scalar()
        or 0
    )
    career_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.request_type.in_(["career", "job"]))
        .scalar()
        or 0
    )
    partner_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.request_type == "partner")
        .scalar()
        or 0
    )
    other_tickets = (
        db.query(func.count(Ticket.id))
        .filter(or_(Ticket.request_type == "other", Ticket.request_type.is_(None)))
        .scalar()
        or 0
    )

    # Кол-во заявок по приоритетам
    p1_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.priority == "P1")
        .scalar()
        or 0
    )
    p2_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.priority == "P2")
        .scalar()
        or 0
    )
    p3_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.priority == "P3")
        .scalar()
        or 0
    )
    p4_tickets = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.priority == "P4")
        .scalar()
        or 0
    )
    auto_closed_percent = (auto_closed_count / total_tickets * 100.0) if total_tickets else 0.0

    # SLA по открытым тикетам (NEW + IN_PROGRESS)
    sla_map = {
        "P1": 30,   # минуты до целевого решения
        "P2": 60,
        "P3": 240,
        "P4": 1440,
    }
    open_sla_ok_tickets = 0
    open_sla_breached_tickets = 0
    open_tickets = (
        db.query(Ticket.priority, Ticket.created_at, Ticket.status)
        .filter(Ticket.status.in_([TicketStatus.NEW.value, TicketStatus.IN_PROGRESS.value]))
        .all()
    )
    for priority, created_at, status in open_tickets:
        if not created_at:
            continue
        target = sla_map.get(priority, 240)
        elapsed_minutes = max((now - created_at).total_seconds() / 60.0, 0.0)
        if elapsed_minutes > target:
            open_sla_breached_tickets += 1
        else:
            open_sla_ok_tickets += 1

    # Упрощённая метрика: пока нет хранения времени первого ответа, берём время до закрытия авто‑тикетов.
    # Считаем разницу в Python, чтобы не зависеть от специфичных SQL‑функций БД.
    avg_first_response_minutes: float | None = None
    if auto_closed_count:
        auto_tickets = (
            db.query(Ticket.created_at, Ticket.closed_at)
            .filter(
                Ticket.status == TicketStatus.AUTO_CLOSED.value,
                Ticket.created_at.isnot(None),
                Ticket.closed_at.isnot(None),
            )
            .all()
        )
        total_seconds = 0.0
        sample_count = 0
        for created_at, closed_at in auto_tickets:
            try:
                delta = (closed_at - created_at).total_seconds()
            except Exception:
                continue
            if delta is not None and delta >= 0:
                total_seconds += delta
                sample_count += 1
        if sample_count:
            avg_first_response_minutes = total_seconds / 60.0 / sample_count

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

    # Авто‑закрытые тикеты, где:
    # 1) пользователь подтвердил авто‑закрытие (status=CLOSED и auto_closed_by_ai=True),
    # 2) оператор ни разу не участвовал в диалоге (нет сообщений с author_type=agent).
    agent_ticket_ids = {
        ticket_id
        for (ticket_id,) in db.query(Message.ticket_id)
        .filter(Message.author_type == AuthorType.AGENT.value)
        .distinct()
        .all()
    }
    user_auto_closed_tickets_query = db.query(func.count(Ticket.id)).filter(
        Ticket.status == TicketStatus.CLOSED.value,
        Ticket.auto_closed_by_ai.is_(True),
    )
    if agent_ticket_ids:
        user_auto_closed_tickets_query = user_auto_closed_tickets_query.filter(
            ~Ticket.id.in_(agent_ticket_ids)
        )
    user_auto_closed_tickets = user_auto_closed_tickets_query.scalar() or 0

    return OverviewMetrics(
        total_tickets=total_tickets,
        new_today=new_today,
        in_progress_tickets=in_progress_tickets,
        closed_today=closed_today,
        auto_closed_percent=auto_closed_percent,
        open_sla_ok_tickets=open_sla_ok_tickets,
        open_sla_breached_tickets=open_sla_breached_tickets,
        user_auto_closed_tickets=user_auto_closed_tickets,
        avg_first_response_minutes=avg_first_response_minutes,
        classification_accuracy=classification_accuracy,
        problem_tickets=problem_tickets,
        question_tickets=question_tickets,
        feedback_tickets=feedback_tickets,
        career_tickets=career_tickets,
        partner_tickets=partner_tickets,
        other_tickets=other_tickets,
        p1_tickets=p1_tickets,
        p2_tickets=p2_tickets,
        p3_tickets=p3_tickets,
        p4_tickets=p4_tickets,
        generated_at=now,
    )
