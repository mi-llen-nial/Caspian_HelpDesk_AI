from app.ai.deepseek_client import get_client
from app.schemas.ai import SummaryResult


def summarize_conversation(text: str, language: str = "ru") -> SummaryResult:
    client = get_client()
    if client is None:
        # Фолбэк: обрезаем текст
        short = text[:500]
        return SummaryResult(summary=short)

    system_prompt = (
        "Ты помощник службы поддержки. Суммируй обращение пользователя "
        f"кратко и по сути на языке {language}. Не больше 3-4 предложений."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
    summary_text = client.chat(messages)
    return SummaryResult(summary=summary_text.strip())

