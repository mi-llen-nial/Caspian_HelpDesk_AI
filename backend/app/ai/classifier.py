from __future__ import annotations

from typing import Optional

from app.ai.deepseek_client import get_client
from app.schemas.ai import ClassificationResult


def classify_text(text: str, request_type: str | None = None) -> ClassificationResult:
    """Классификация тикета.

    Если DeepSeek недоступен или ключ не указан, используем простую
    эвристику, чтобы сервис оставался рабочим.
    """

    client = get_client()
    if client is None:
        # Простейшая эвристика: всё идёт в IT-SERVICE, приоритет P3
        return ClassificationResult(
            category_code="GENERAL",
            department_code="IT-SERVICE",
            priority="P3",
            language="ru",
            auto_resolvable=False,
            confidence=0.5,
        )

    base_prompt = (
        "Ты ИИ-ассистент для маршрутизации заявок в службу поддержки. "
        "По входному тексту определи: код категории, код департамента, "
        "приоритет (P1-P4), язык (ru или kk) и можно ли автоматически "
        "решить запрос. Верни строго JSON с полями: "
        "category_code, department_code, priority, language, "
        "auto_resolvable, confidence (0-1). "
        "Поле category_code — это код подкатегории (машиночитаемый ключ), "
        "например CONNECTION_WIFI, CONNECTION_TV, INTERNET_HOME, INTERNET_MOBILE, "
        "BILLING_TARIFF, ACCOUNT_BALANCE, SUPPORT_GENERAL и т.п. "
        "Не используй пробелы и русские символы в category_code, только латинские буквы, цифры и подчёркивания. "
        "Поле department_code — это код департамента, выбирай один из: "
        "technical_support (техподдержка интернета и ИТ-услуг), "
        "tv_support (поддержка ТВ и IPTV), "
        "billing (биллинг, оплата, тарифы), "
        "sales (подключения и продажи), "
        "customer_care (общие вопросы и обращения), "
        "hr (работа и стажировки), "
        "partnership (партнёрство и сотрудничество). "
        "Выбирай наиболее подходящий департамент исходя из сути обращения."
    )

    if request_type:
        base_prompt += (
            f" Тип обращения (категория, выбранная пользователем): {request_type}. "
            "Учитывай это при выборе категории и приоритета. "
            "Примеры: problem или difficulty — это техническая проблема/что-то не работает; "
            "question — это просто вопрос или запрос информации; "
            "feedback или proposal — это предложение или отзыв (не инцидент, не неисправность); "
            "career или job — это трудоустройство и стажировки; "
            "partner — партнёрство и сотрудничество; other — другое."
        )

    system_prompt = base_prompt

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]

    data = client.chat_json(messages)
    return ClassificationResult(**data)
