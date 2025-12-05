from app.ai.deepseek_client import get_client
from app.schemas.ai import ReplySuggestions


def suggest_replies(
    conversation_text: str,
    language: str = "ru",
    request_type: str | None = None,
    max_suggestions: int = 3,
) -> ReplySuggestions:
    """Генерация нескольких вариантов ответа для оператора второй линии."""

    client = get_client()
    if client is None:
        return ReplySuggestions(suggestions=[])

    if language == "ru":
        base_instruction = (
            "Ты помощник оператора второй линии поддержки. "
            "На основе истории диалога предложи несколько (до "
            f"{max_suggestions} штук) коротких и конкретных вариантов ответа оператору. "
            "Ответы должны быть полезны пользователю и относиться к его проблеме. "
            "Пиши формулировки так, чтобы оператор мог отправить их клиенту без правок "
            "или с минимальными изменениями. "
            "Верни строго JSON вида {\"suggestions\": [\"...\", \"...\", ...]} без дополнительного текста."
        )
    elif language == "kk":
        base_instruction = (
            "Сен екінші деңгейдегі қолдау операторының көмекшісісің. "
            "Диалог тарихына сүйеніп, оператор клиентке жібере алатын "
            f"{max_suggestions} қысқа және нақты жауап нұсқасын ұсын. "
            "Тек JSON қайтар: {\"suggestions\": [\"...\", \"...\"]}."
        )
    else:
        base_instruction = (
            "You are a helper for a level 2 support agent. "
            f"Based on the conversation history, propose up to {max_suggestions} short reply options "
            "the agent could send to the user. "
            "Return strictly JSON: {\"suggestions\": [\"...\", \"...\"]}."
        )

    if request_type:
        base_instruction += f" Request type hint: {request_type}."

    messages = [
        {"role": "system", "content": base_instruction},
        {"role": "user", "content": conversation_text},
    ]

    data = client.chat_json(messages)
    return ReplySuggestions(**data)

