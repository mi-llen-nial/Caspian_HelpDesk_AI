import logging
from typing import Union

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_text_message(chat_id: Union[int, str], text: str) -> None:
    """Отправка простого текстового сообщения пользователю в Telegram.

    Используется для ручных ответов операторов из веб‑интерфейса.
    Ошибки логируются, но не ломают основной поток обработки.
    """

    settings = get_settings()
    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not configured; skipping Telegram send")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send Telegram message to chat_id=%s", chat_id)

