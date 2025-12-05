from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.classifier import classify_text
from app.ai.answer_generator import generate_answer
from app.models.department import Department
from app.models.message import AuthorType, Message
from app.models.model_log import ModelLog
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import ExternalTicketCreate, TicketCreate
from app.services.faq_service import get_best_match


AUTO_CLOSE_CONFIDENCE_THRESHOLD = 0.8


def _get_or_create_department(db: Session, code: str) -> Department:
    department = db.query(Department).filter(Department.code == code).first()
    if department:
        return department

    department = Department(code=code, name=code)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def process_new_ticket(db: Session, data: TicketCreate) -> Ticket:
    """Создание тикета с автоматической классификацией и возможным авто‑закрытием."""

    text = f"{data.subject}\n\n{data.description}"
    classification = classify_text(text, request_type=data.request_type)

    # Небольшая коррекция категории по ключевым словам,
    # чтобы, например, запросы про телевидение не попадали в интернет-шаблоны.
    lower_text = text.lower()
    if any(kw in lower_text for kw in ("телевиден", "тв ", "iptv", "tv ", "телеканал", "канал ")):
        if "интернет" not in lower_text:
            classification.category_code = "CONNECTION_TV"

    department = _get_or_create_department(db, classification.department_code)

    now = datetime.utcnow()
    ticket = Ticket(
        subject=data.subject,
        description=data.description,
        channel=data.channel,
        language=classification.language or data.language,
        customer_email=data.customer_email,
        customer_username=data.customer_username,
        external_user_id=data.external_user_id,
        request_type=data.request_type,
        category_code=classification.category_code,
        priority=classification.priority,
        status=TicketStatus.NEW.value,
        department_id=department.id,
        auto_closed_by_ai=False,
        ai_disabled=False,
        status_updated_at=now,
    )
    db.add(ticket)
    db.flush()

    # Первое сообщение от клиента
    message = Message(
        ticket_id=ticket.id,
        author_type=AuthorType.CUSTOMER.value,
        body=data.description,
        language=data.language,
    )
    db.add(message)

    # Логируем запрос к модели
    db.add(
        ModelLog(
            ticket_id=ticket.id,
            model_name="deepseek",
            input_type="classification",
            request_payload=text,
            response_payload=classification.json(),
            confidence=classification.confidence,
            was_corrected=0,
        )
    )

    # Попытка авто‑закрытия
    if classification.auto_resolvable and classification.confidence >= AUTO_CLOSE_CONFIDENCE_THRESHOLD:
        faq = get_best_match(
            db,
            classification.category_code,
            classification.language,
            request_type=data.request_type,
        )
        if faq:
            # Если есть подходящий шаблон, используем его напрямую
            answer_text = faq.answer
            answer_lang = faq.language
        else:
            faq_snippet = None
            suggestion = generate_answer(
                text,
                language=classification.language,
                faq_snippet=faq_snippet,
                request_type=data.request_type,
            )
            answer_text = suggestion.answer
            answer_lang = suggestion.answer_language

        ai_message = Message(
            ticket_id=ticket.id,
            author_type=AuthorType.AI.value,
            body=answer_text,
            language=answer_lang,
        )
        db.add(ai_message)

        now = datetime.utcnow()
        ticket.status = TicketStatus.AUTO_CLOSED.value
        ticket.auto_closed_by_ai = True
        ticket.closed_at = now
        ticket.status_updated_at = now

    db.commit()
    db.refresh(ticket)
    return ticket


def create_placeholder_telegram_ticket(
    db: Session,
    subject: str,
    chat_id: int,
    username: str | None,
    language: str,
    request_type: str,
) -> Ticket:
    """Создаёт пустой тикет для Telegram после выбора категории.

    Описание и классификация появятся после первого сообщения пользователя.
    """

    ticket = Ticket(
        subject=subject,
        description="",
        channel="telegram",
        language=language,
        customer_email=None,
        customer_username=username,
        external_user_id=str(chat_id),
        request_type=request_type,
        category_code=None,
        priority="P3",
        status=TicketStatus.NEW.value,
        department_id=None,
        auto_closed_by_ai=False,
        ai_disabled=False,
        status_updated_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def continue_telegram_ticket(
    db: Session,
    ticket: Ticket,
    message_text: str,
    language: str,
) -> Ticket:
    """Обрабатывает новое сообщение пользователя в существующем Telegram‑тикете.

    Выполняет классификацию, создаёт сообщение клиента, ищет FAQ и формирует
    ответ от ИИ, но не закрывает тикет автоматически.
    """

    # Сообщение от клиента
    msg = Message(
        ticket_id=ticket.id,
        author_type=AuthorType.CUSTOMER.value,
        body=message_text,
        language=language,
    )
    db.add(msg)

    text = f"{ticket.subject}\n\n{message_text}"
    classification = classify_text(text, request_type=ticket.request_type)

    lower_text = text.lower()
    if any(kw in lower_text for kw in ("телевиден", "тв ", "iptv", "tv ", "телеканал", "канал ")):
        if "интернет" not in lower_text:
            classification.category_code = "CONNECTION_TV"

    # Обновляем департамент и параметры тикета
    department = _get_or_create_department(db, classification.department_code)

    ticket.description = message_text
    ticket.language = language or classification.language or ticket.language or "ru"
    ticket.category_code = classification.category_code
    ticket.priority = classification.priority
    ticket.department_id = department.id

    # Переводим тикет в работу только один раз, чтобы
    # корректно считать время в этом статусе.
    if ticket.status != TicketStatus.IN_PROGRESS.value:
        ticket.status = TicketStatus.IN_PROGRESS.value
        ticket.status_updated_at = datetime.utcnow()

    # Логируем классификацию
    db.add(
        ModelLog(
            ticket_id=ticket.id,
            model_name="deepseek",
            input_type="classification",
            request_payload=text,
            response_payload=classification.json(),
            confidence=classification.confidence,
            was_corrected=0,
        )
    )

    # Если для тикета отключены авто‑ответы ИИ, не формируем AI‑сообщение
    if not ticket.ai_disabled:
        # FAQ и ответ: сначала пробуем шаблон, затем ИИ
        faq = get_best_match(
            db,
            classification.category_code,
            ticket.language,
            request_type=ticket.request_type,
        )

        if faq:
            answer_text = faq.answer
            answer_lang = faq.language
        else:
            faq_snippet = None
            suggestion = generate_answer(
                text,
                language=ticket.language,
                faq_snippet=faq_snippet,
                request_type=ticket.request_type,
            )
            answer_text = suggestion.answer
            answer_lang = suggestion.answer_language

        ai_message = Message(
            ticket_id=ticket.id,
            author_type=AuthorType.AI.value,
            body=answer_text,
            language=answer_lang,
        )
        db.add(ai_message)

    db.commit()
    db.refresh(ticket)
    return ticket


def create_ticket_from_external(db: Session, data: ExternalTicketCreate) -> Ticket:
    """Создание тикета внешним источником (например, обработчиком почты).

    Классификация и статусы уже определены внешней системой.
    """

    department_id = None
    if data.department_code:
        department = _get_or_create_department(db, data.department_code)
        department_id = department.id

    now = datetime.utcnow()
    ticket = Ticket(
        subject=data.subject,
        description=data.description,
        channel=data.channel,
        language=data.language,
        customer_email=data.customer_email,
        customer_username=data.customer_username,
        external_user_id=data.external_user_id,
        request_type=data.request_type,
        category_code=data.category_code,
        priority=data.priority,
        status=data.status,
        department_id=department_id,
        auto_closed_by_ai=data.status == TicketStatus.AUTO_CLOSED.value,
        ai_disabled=False,
        status_updated_at=now,
    )
    db.add(ticket)
    db.flush()

    # Первое сообщение от клиента
    message = Message(
        ticket_id=ticket.id,
        author_type=AuthorType.CUSTOMER.value,
        body=data.description,
        language=data.language,
    )
    db.add(message)

    db.commit()
    db.refresh(ticket)
    return ticket
