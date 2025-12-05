from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import get_settings


class DeepSeekClient:
    """Клиент для работы с DeepSeek API.

    По умолчанию использует OpenAI-совместимый эндпоинт:
    https://api.deepseek.com/v1/chat/completions
    Настоящий URL/модель можно переопределить в настройках.
    """

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.deepseek_api_key

        # Базовый URL: если в .env указан https://api.deepseek.com,
        # автоматически добавляем /v1.
        base = str(settings.deepseek_base_url or "https://api.deepseek.com")
        base = base.rstrip("/")
        if not base.endswith("/v1"):
            base = base + "/v1"
        self.base_url = base

        self.model = settings.deepseek_model

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise RuntimeError("DeepSeek API key is not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages: List[Dict[str, str]], **extra: Any) -> str:
        """Базовый вызов chat-комплишена, возвращает текст первого ответа."""

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": extra.get("temperature", 0.1),
        }
        url = f"{self.base_url}/chat/completions"

        with httpx.Client(timeout=extra.get("timeout", 15.0)) as client:
            response = client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            data = response.json()

        # Ожидаемый OpenAI-совместимый формат
        return data["choices"][0]["message"]["content"]

    def chat_json(self, messages: List[Dict[str, str]], **extra: Any) -> Dict[str, Any]:
        """Чат с требованием вернуть корректный JSON. Пытается распарсить ответ."""

        content = self.chat(messages, **extra)
        # На всякий случай вырезаем обёртку ```json ... ```
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:]
        return json.loads(content)


def get_client() -> Optional[DeepSeekClient]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        return None
    return DeepSeekClient()
