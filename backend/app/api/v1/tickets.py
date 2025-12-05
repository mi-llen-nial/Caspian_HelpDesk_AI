from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.message import AuthorType, Message
from app.models.ticket import Ticket, TicketStatus
from app.integrations.telegram_sender import send_text_message
from app.ai.summarizer import summarize_conversation
from app.ai.reply_suggester import suggest_replies
from app.schemas.ai import SummaryResult, ReplySuggestions
from app.schemas.ticket import (
    ExternalTicketCreate,
    MessageCreate,
    MessageRead,
    TicketCreate,
    TicketDetails,
    TicketRead,
    TicketStatusUpdate,
)
from app.services.routing_service import create_ticket_from_external, process_new_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead)
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    ticket = process_new_ticket(db, data)
    return _ticket_to_read(ticket)


@router.get("", response_model=List[TicketRead])
def list_tickets(
    db: Session = Depends(get_db),
    status: str | None = Query(None),
    channel: str | None = Query(None),
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if channel:
        query = query.filter(Ticket.channel == channel)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return [_ticket_to_read(t) for t in tickets]


@router.post("/external", response_model=TicketRead)
def create_ticket_external(data: ExternalTicketCreate, db: Session = Depends(get_db)):
    """Создание тикета внешним источником (например, обработчиком почты Outlook).

    Здесь предполагается, что статус, приоритет и классификация уже определены внешней системой.
    """

    ticket = create_ticket_from_external(db, data)
    return _ticket_to_read(ticket)


@router.get("/{ticket_id}", response_model=TicketDetails)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket: Ticket | None = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return TicketDetails(
        **_ticket_to_read(ticket).dict(),
        messages=[
            MessageRead.from_orm(m) for m in sorted(ticket.messages, key=lambda mm: mm.created_at)
        ],
    )


@router.post("/{ticket_id}/messages", response_model=MessageRead)
def add_message(ticket_id: int, data: MessageCreate, db: Session = Depends(get_db)):
    ticket: Ticket | None = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    msg = Message(
        ticket_id=ticket_id,
        author_type=data.author_type or AuthorType.AGENT.value,
        body=data.body,
        language=data.language,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Если это ответ оператора по Telegram‑тикету — отправляем его в чат пользователю
    if (
        ticket.channel == "telegram"
        and msg.author_type == AuthorType.AGENT.value
        and ticket.external_user_id
    ):
        try:
            send_text_message(ticket.external_user_id, msg.body)
        except Exception:
            # Не ломаем API, если отправка в Telegram не удалась
            import logging

            logging.getLogger(__name__).exception(
                "Failed to deliver agent message to Telegram for ticket %s", ticket_id
            )

    return MessageRead.from_orm(msg)


@router.put("/{ticket_id}/status", response_model=TicketRead)
def update_ticket_status(
    ticket_id: int,
    data: TicketStatusUpdate,
    db: Session = Depends(get_db),
):
    """Обновление статуса тикета вручную из интерфейса оператора."""

    ticket: Ticket | None = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_status = ticket.status

    if data.status not in {
        TicketStatus.NEW.value,
        TicketStatus.IN_PROGRESS.value,
        TicketStatus.CLOSED.value,
        TicketStatus.AUTO_CLOSED.value,
    }:
        raise HTTPException(status_code=400, detail="Unsupported ticket status")

    ticket.status = data.status

    if data.status in {TicketStatus.CLOSED.value, TicketStatus.AUTO_CLOSED.value}:
        now = datetime.utcnow()
        ticket.closed_at = now
        ticket.status_updated_at = now
    else:
        ticket.closed_at = None

    # Ручное изменение — считаем, что это не авто‑закрытие
    if data.status != TicketStatus.AUTO_CLOSED.value:
        ticket.auto_closed_by_ai = False

    # Если статус изменился (например, NEW → IN_PROGRESS), фиксируем момент смены
    if data.status != old_status and data.status not in {
        TicketStatus.CLOSED.value,
        TicketStatus.AUTO_CLOSED.value,
    }:
        ticket.status_updated_at = datetime.utcnow()

    if data.priority is not None:
        ticket.priority = data.priority

    if data.request_type is not None:
        ticket.request_type = data.request_type

    if data.ai_disabled is not None:
        ticket.ai_disabled = data.ai_disabled

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _ticket_to_read(ticket)


@router.get("/{ticket_id}/summary", response_model=SummaryResult)
def get_ticket_summary(ticket_id: int, db: Session = Depends(get_db)) -> SummaryResult:
    """Краткое резюме диалога по тикету для второй линии."""

    ticket: Ticket | None = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    messages = (
        db.query(Message)
        .filter(Message.ticket_id == ticket_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if messages:
        parts: list[str] = []
        for m in messages:
            role = m.author_type
            ts = m.created_at.strftime("%Y-%m-%d %H:%M")
            parts.append(f"{role} ({ts}): {m.body}")
        text = "\n".join(parts)
    else:
        text = ticket.description or ""

    language = ticket.language or "ru"
    return summarize_conversation(text, language=language)


@router.get("/{ticket_id}/reply_suggestions", response_model=ReplySuggestions)
def get_ticket_reply_suggestions(
    ticket_id: int, db: Session = Depends(get_db)
) -> ReplySuggestions:
    """Сгенерировать несколько вариантов ответа для оператора."""

    ticket: Ticket | None = db.query(Ticket).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    messages = (
        db.query(Message)
        .filter(Message.ticket_id == ticket_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if messages:
        parts: list[str] = []
        for m in messages:
            role = m.author_type
            ts = m.created_at.strftime("%Y-%m-%d %H:%M")
            parts.append(f"{role} ({ts}): {m.body}")
        text = "\n".join(parts)
    else:
        text = ticket.description or ""

    language = ticket.language or "ru"
    return suggest_replies(
        conversation_text=text,
        language=language,
        request_type=ticket.request_type,
    )


def _ticket_to_read(ticket: Ticket) -> TicketRead:
    department_name = ticket.department.name if ticket.department else None
    department_code = ticket.department.code if ticket.department else None
    # SLA: простое правило по приоритету
    sla_map = {
        "P1": 30,   # минуты до целевого решения
        "P2": 60,
        "P3": 240,
        "P4": 1440,
    }
    sla_target = sla_map.get(ticket.priority, 240)
    now = datetime.utcnow()
    end_ts = ticket.closed_at or now
    elapsed_minutes = max((end_ts - ticket.created_at).total_seconds() / 60.0, 0.0)
    sla_breached = elapsed_minutes > sla_target and ticket.status not in {
        TicketStatus.CLOSED.value,
        TicketStatus.AUTO_CLOSED.value,
    }

    # Время в текущем статусе: считаем от момента последнего изменения статуса
    status_changed_at = ticket.status_updated_at or ticket.created_at
    status_end_ts = ticket.closed_at or now
    status_elapsed_minutes = max(
        (status_end_ts - status_changed_at).total_seconds() / 60.0,
        0.0,
    )
    return TicketRead(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        channel=ticket.channel,
        language=ticket.language,
        request_type=ticket.request_type,
        customer_email=ticket.customer_email,
        customer_username=ticket.customer_username,
        category_code=ticket.category_code,
        priority=ticket.priority,
        status=ticket.status,
        department_code=department_code,
        department_name=department_name,
        auto_closed_by_ai=ticket.auto_closed_by_ai,
        ai_disabled=ticket.ai_disabled,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        closed_at=ticket.closed_at,
        sla_target_minutes=sla_target,
        sla_elapsed_minutes=elapsed_minutes,
        sla_breached=sla_breached,
        status_elapsed_minutes=status_elapsed_minutes,
    )
