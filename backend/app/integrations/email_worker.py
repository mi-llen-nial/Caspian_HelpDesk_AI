import email
import imaplib
import logging
import re
import smtplib
import time
from email.header import decode_header, make_header
from email.message import EmailMessage
from typing import Optional

from datetime import datetime, timedelta

from app.ai.answer_generator import generate_answer
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.message import AuthorType, Message as DbMessage
from app.models.ticket import Ticket, TicketStatus
from app.services.routing_service import continue_telegram_ticket, process_new_ticket
from app.schemas.ticket import TicketCreate

logger = logging.getLogger(__name__)

TICKET_ID_PATTERN = re.compile(r"\[HD-(\d+)\]")


def _decode_mime_header(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_plain_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = (part.get("Content-Disposition") or "").lower()
            if content_type == "text/plain" and "attachment" not in disposition:
                charset = part.get_content_charset() or "utf-8"
                try:
                    return part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    continue
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            return msg.get_payload(decode=True).decode(charset, errors="replace")
        except Exception:
            return msg.get_payload()
    return ""


def _detect_language(text: str, fallback: str = "ru") -> str:
    has_cyrillic = any("а" <= ch <= "я" or "А" <= ch <= "Я" for ch in text)
    kazakh_chars = set("әіңғүұқөһӘІҢҒҮҰҚӨҺ")
    has_kazakh = any(ch in kazakh_chars for ch in text)
    if has_kazakh:
        return "kk"
    if has_cyrillic:
        return "ru"
    return fallback or "ru"


def _parse_ticket_id_from_subject(subject: str) -> Optional[int]:
    match = TICKET_ID_PATTERN.search(subject or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _build_reply_subject(original_subject: str, ticket_id: int) -> str:
    tag = f"[HD-{ticket_id}]"
    if tag in (original_subject or ""):
        return original_subject
    if original_subject.lower().startswith("re:"):
        return f"{original_subject} {tag}"
    return f"Re: {original_subject} {tag}".strip()


def _send_email_reply(
    to_address: str,
    subject: str,
    body: str,
) -> None:
    settings = get_settings()
    if not settings.email_username or not settings.email_password:
        logger.warning("Email credentials are not configured; reply is skipped")
        return

    msg = EmailMessage()
    from_display = settings.email_from_name or settings.email_username
    msg["From"] = f"{from_display} <{settings.email_username}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.email_username, settings.email_password)
        smtp.send_message(msg)


def _handle_new_email_message(
    db,
    from_address: str,
    subject: str,
    body: str,
) -> None:
    settings = get_settings()

    if from_address.lower() == (settings.email_username or "").lower():
        # Это наше собственное письмо — не создаём тикет
        return

    ticket_id = _parse_ticket_id_from_subject(subject)
    language = _detect_language(body or subject or "")

    if ticket_id is not None:
        ticket: Ticket | None = db.query(Ticket).get(ticket_id)
        if ticket and ticket.channel == "email":
            # Продолжение существующего email‑тикета
            updated_ticket = continue_telegram_ticket(
                db=db,
                ticket=ticket,
                message_text=body,
                language=language,
            )
            # Находим последний AI‑ответ, чтобы отправить его по почте
            ai_message = (
                db.query(DbMessage)
                .filter(
                    DbMessage.ticket_id == updated_ticket.id,
                    DbMessage.author_type == AuthorType.AI.value,
                )
                .order_by(DbMessage.created_at.desc())
                .first()
            )
            if ai_message:
                reply_subject = _build_reply_subject(subject, updated_ticket.id)
                _send_email_reply(
                    to_address=from_address,
                    subject=reply_subject,
                    body=ai_message.body,
                )
            return

    # Новый тикет из письма
    ticket_in = TicketCreate(
        subject=subject or "(без темы)",
        description=body or "",
        channel="email",
        language=language,
        customer_email=from_address,
        customer_username=None,
        external_user_id=None,
        request_type=None,
    )
    ticket = process_new_ticket(db, ticket_in)

    # Проверяем, есть ли авто‑ответ от модели при авто‑закрытии
    ai_message = (
        db.query(DbMessage)
        .filter(
            DbMessage.ticket_id == ticket.id,
            DbMessage.author_type == AuthorType.AI.value,
        )
        .order_by(DbMessage.created_at.desc())
        .first()
    )

    if ai_message:
        answer_text = ai_message.body
    else:
        # Генерируем развернутый ответ по аналогии с Telegram
        full_text = f"Email от клиента: {from_address}\nТема: {subject}\n\nТекст обращения:\n{body}"
        suggestion = generate_answer(
            full_text,
            language=ticket.language or language,
            faq_snippet=None,
            request_type=ticket.request_type,
        )
        ai_message = DbMessage(
            ticket_id=ticket.id,
            author_type=AuthorType.AI.value,
            body=suggestion.answer,
            language=suggestion.answer_language,
        )
        db.add(ai_message)
        db.commit()
        answer_text = suggestion.answer

    reply_subject = _build_reply_subject(subject, ticket.id)
    _send_email_reply(
        to_address=from_address,
        subject=reply_subject,
        body=answer_text,
    )


def _auto_close_stale_email_tickets(db, inactivity_minutes: int = 60) -> None:
    """Авто‑закрытие email‑тикетов при отсутствии новых писем от клиента.

    Логика:
    - берём тикеты канала email, которые ещё не закрыты;
    - находим последнее сообщение клиента и последнее сообщение оператора/ИИ;
    - если последнее сообщение в тикете не от клиента (то есть мы уже ответили)
      и с момента последнего сообщения клиента прошло больше inactivity_minutes,
      считаем, что диалог можно закрыть автоматически.
    """

    threshold = datetime.utcnow() - timedelta(minutes=inactivity_minutes)

    open_tickets = (
        db.query(Ticket)
        .filter(
            Ticket.channel == "email",
            Ticket.status.in_([TicketStatus.NEW.value, TicketStatus.IN_PROGRESS.value]),
        )
        .all()
    )

    for ticket in open_tickets:
        customer_msg = (
            db.query(DbMessage)
            .filter(
                DbMessage.ticket_id == ticket.id,
                DbMessage.author_type == AuthorType.CUSTOMER.value,
            )
            .order_by(DbMessage.created_at.desc())
            .first()
        )
        last_msg = (
            db.query(DbMessage)
            .filter(DbMessage.ticket_id == ticket.id)
            .order_by(DbMessage.created_at.desc())
            .first()
        )

        if not customer_msg or not last_msg:
            continue

        # Если последнее сообщение от клиента — нельзя считать тикет закрытым
        if last_msg.author_type == AuthorType.CUSTOMER.value:
            continue

        # Если с момента последнего клиентского сообщения прошло больше порога — закрываем
        if customer_msg.created_at <= threshold:
            ticket.status = TicketStatus.AUTO_CLOSED.value
            ticket.auto_closed_by_ai = True
            ticket.closed_at = datetime.utcnow()
            db.add(ticket)

    db.commit()


def poll_email_once() -> None:
    """Однократная обработка новых писем в Outlook."""

    settings = get_settings()
    if not (settings.email_enabled and settings.email_username and settings.email_password):
        logger.info("Email polling is disabled or not configured")
        return

    mail = imaplib.IMAP4_SSL(settings.email_imap_host, settings.email_imap_port)
    try:
        mail.login(settings.email_username, settings.email_password)
        mail.select("INBOX")

        status, data = mail.search(None, "UNSEEN")
        if status != "OK":
            logger.warning("Failed to search UNSEEN emails: %s", status)
            return

        ids = data[0].split()
        if not ids:
            return

        db = SessionLocal()
        try:
            for email_id in ids:
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    raw_subject = msg.get("Subject", "")
                    subject = _decode_mime_header(raw_subject)
                    from_header = msg.get("From", "")
                    from_address = email.utils.parseaddr(from_header)[1]
                    body = _extract_plain_text(msg).strip()

                    _handle_new_email_message(
                        db=db,
                        from_address=from_address,
                        subject=subject,
                        body=body,
                    )

                    # Помечаем письмо прочитанным
                    mail.store(email_id, "+FLAGS", "\\Seen")
                except Exception:
                    logger.exception("Failed to process email message id=%s", email_id)

            # После обработки входящих писем пробуем авто‑закрыть "тихие" тикеты
            _auto_close_stale_email_tickets(db)
        finally:
            db.close()
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def main_loop(poll_interval_seconds: int = 5) -> None:
    """Простой цикл опроса почты.

    Запуск:
        python -m app.integrations.email_worker
    """

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
    logger.info("Starting Outlook email worker")
    while True:
        try:
            poll_email_once()
        except Exception:
            logger.exception("Error while polling email")
        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    main_loop()
