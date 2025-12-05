import asyncio
import logging
from typing import Dict

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.ai.answer_generator import generate_answer
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.message import AuthorType, Message as DbMessage
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCreate
from app.services.routing_service import (
    continue_telegram_ticket,
    create_placeholder_telegram_ticket,
    process_new_ticket,
)
from app.services.faq_service import get_best_match

logger = logging.getLogger(__name__)


CATEGORY_CHOICES: Dict[str, str] = {
    "problem": "Что-то не работает",
    "question": "У меня есть вопрос",
    "feedback": "Предложение или отзыв",
    "career": "Работа и стажировки",
    "partner": "Партнёрство и сотрудничество",
    "other": "Другое",
}

# Простое in‑memory состояние: ключ — chat_id, значение — данные сессии
USER_STATE: Dict[int, Dict[str, str]] = {}


def build_answer_with_greeting(first_name: str | None, answer: str) -> str:
    """Добавляет персональное приветствие к ответу ИИ."""

    name_part = (first_name or "").strip()
    if name_part:
        prefix = (
            f"{name_part}, ваш запрос обработан. "
            "Мы предлагаем вам следующее решение:\n\n"
        )
    else:
        prefix = "Ваш запрос обработан. Мы предлагаем вам следующее решение:\n\n"
    return prefix + (answer or "")


def detect_language_from_text(text: str, fallback: str = "ru") -> str:
  """Простейшая детекция языка по алфавиту."""
  has_cyrillic = any("а" <= ch <= "я" or "А" <= ch <= "Я" for ch in text)
  kazakh_chars = set("әіңғүұқөһӘІҢҒҮҰҚӨҺ")
  has_kazakh = any(ch in kazakh_chars for ch in text)
  if has_kazakh:
      return "kk"
  if has_cyrillic:
      return "ru"
  return fallback or "ru"


async def cmd_start(message: Message) -> None:
    keyboard = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"category:{key}",
            )
        ]
        for key, label in CATEGORY_CHOICES.items()
    ]
    await message.answer(
        f"Здравствуйте, {message.from_user.first_name}! \n\nЯ ваш личный асситент от компании Казахтелеком \n\nПожалуйста выберите категорию которая соответствует вашему запросу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


async def handle_category(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        return

    _, category_key = callback.data.split(":", 1)
    chat_id = callback.message.chat.id
    user = callback.from_user

    language = (user.language_code or "ru")[:2] if user and user.language_code else "ru"

    # Создаём пустой лид сразу после выбора категории
    db = SessionLocal()
    try:
        username = user.username if user else None
        subject = CATEGORY_CHOICES.get(category_key, "Обращение")
        ticket = create_placeholder_telegram_ticket(
            db=db,
            subject=subject,
            chat_id=chat_id,
            username=username,
            language=language,
            request_type=category_key,
        )
        USER_STATE[chat_id] = {
            "category_key": category_key,
            "language": language,
            "ticket_id": str(ticket.id),
        }
    finally:
        db.close()

    await callback.message.edit_text("Пожалуйста, опишите вашу проблему/вопрос одним сообщением.")
    await callback.answer()


async def handle_text(message: Message) -> None:
    if not message.text:
        return

    chat_id = message.chat.id
    text = message.text.strip()
    if not text:
        return

    state = USER_STATE.get(chat_id)
    if not state:
        await message.answer("Для начала выберите тип обращения с помощью /start.")
        return

    ui_language = state.get("language") or "ru"
    category_key = state.get("category_key") or "other"

    # Быстрый индикатор обработки, пока генерируется ответ
    if ui_language.startswith("kk"):
        processing_text = "Сұрауыңыз өңделуде, 5–30 секунд күтіңіз."
    else:
        processing_text = "Запрос в обработке... \n\nПожалуйста подождите 5–30 секунд."
    processing_msg = await message.answer(processing_text)

    msg_language = detect_language_from_text(text, ui_language)

    subject = CATEGORY_CHOICES.get(category_key, "Обращение")
    description = text
    username = message.from_user.username if message.from_user else None
    user_id = message.from_user.id if message.from_user else None

    db = SessionLocal()
    try:
        ticket: Ticket | None = None
        ticket_id_str = state.get("ticket_id")
        if ticket_id_str:
            ticket = db.query(Ticket).get(int(ticket_id_str))

        if ticket is None:
            # На всякий случай создаём тикет, если по какой‑то причине его ещё нет
            ticket_in = TicketCreate(
                subject=subject,
                description=description,
                channel="telegram",
                language=msg_language,
                customer_email=None,
                customer_username=username,
                external_user_id=str(user_id) if user_id is not None else None,
                request_type=category_key,
            )
            ticket = process_new_ticket(db, ticket_in)
            USER_STATE[chat_id]["ticket_id"] = str(ticket.id)
        else:
            ticket = continue_telegram_ticket(
                db=db,
                ticket=ticket,
                message_text=description,
                language=msg_language,
            )

        # Проверяем, создал ли AI авто‑ответ при авто‑закрытии
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
            # Дополнительный ответ, если AI‑сообщение не было создано
            try:
                faq = get_best_match(
                    db,
                    ticket.category_code,
                    ticket.language,
                    request_type=ticket.request_type,
                )
            except Exception:
                faq = None

            if faq:
                answer_text = faq.answer
                ai_message = DbMessage(
                    ticket_id=ticket.id,
                    author_type=AuthorType.AI.value,
                    body=answer_text,
                    language=faq.language,
                )
                db.add(ai_message)
                db.commit()
            else:
                full_text = f"Категория обращения (выбрана пользователем): {subject}\n\nСообщение клиента:\n{description}"
                answer_language = ticket.language or msg_language
                suggestion = generate_answer(
                    full_text,
                    language=answer_language,
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
    except Exception:
        logger.exception("Ошибка при обработке сообщения Telegram")
        answer_text = "Произошла ошибка при обработке обращения. Попробуйте позже."
    finally:
        db.close()

    # Заменяем сообщение «запрос в обработке» финальным ответом
    first_name = message.from_user.first_name if message.from_user else None
    final_text = build_answer_with_greeting(first_name, answer_text)
    try:
        await processing_msg.edit_text(final_text)
    except Exception:
        # Если редактирование не удалось (например, сообщение удалено),
        # отправляем ответ отдельным сообщением.
        await message.answer(final_text)

    # Спрашиваем, помог ли ответ
    if ticket and ticket.status != TicketStatus.CLOSED.value:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Да, спасибо", callback_data=f"close:{ticket.id}"
                    ),
                    InlineKeyboardButton(
                        text="Нет, продолжить", callback_data=f"continue:{ticket.id}"
                    ),
                ]
            ]
        )
        await message.answer("Подскажите, вы получили ответ на свой вопрос?", reply_markup=kb)


async def handle_close(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        return
    _, ticket_id_str = callback.data.split(":", 1)
    chat_id = callback.message.chat.id

    db = SessionLocal()
    try:
        ticket = db.query(Ticket).get(int(ticket_id_str))
        if ticket:
            ticket.status = TicketStatus.CLOSED.value
            ticket.auto_closed_by_ai = True
            from datetime import datetime

            now = datetime.utcnow()
            ticket.closed_at = now
            ticket.status_updated_at = now
            db.commit()
        USER_STATE.pop(chat_id, None)
    finally:
        db.close()

    await callback.message.edit_text("Спасибо! Сессия закрыта. Если возникнут новые вопросы, напишите нам снова.")
    await callback.answer()


async def handle_continue(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        return
    chat_id = callback.message.chat.id
    await callback.message.edit_text(
        "Хорошо, напишите, пожалуйста, что ещё осталось непонятно или опишите новую проблему."
    )
    await callback.answer()


async def main() -> None:
    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN не настроен. Добавьте его в backend/.env или переменные окружения."
        )

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
    logger.info("Запуск Telegram-бота HelpDeskAI (aiogram)")

    bot = Bot(token=token)
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(handle_category, F.data.startswith("category:"))
    dp.callback_query.register(handle_close, F.data.startswith("close:"))
    dp.callback_query.register(handle_continue, F.data.startswith("continue:"))
    dp.message.register(handle_text, F.text)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
