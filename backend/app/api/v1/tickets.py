from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.message import AuthorType, Message
from app.models.ticket import Ticket
from app.integrations.telegram_sender import send_text_message
from app.schemas.ticket import (
    MessageCreate,
    MessageRead,
    TicketCreate,
    TicketDetails,
    ExternalTicketCreate,
    TicketRead,
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


def _ticket_to_read(ticket: Ticket) -> TicketRead:
    department_name = ticket.department.name if ticket.department else None
    return TicketRead(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        channel=ticket.channel,
        language=ticket.language,
        customer_email=ticket.customer_email,
        customer_username=ticket.customer_username,
        category_code=ticket.category_code,
        priority=ticket.priority,
        status=ticket.status,
        department_name=department_name,
        auto_closed_by_ai=ticket.auto_closed_by_ai,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        closed_at=ticket.closed_at,
    )
