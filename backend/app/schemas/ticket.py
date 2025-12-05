from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class MessageBase(BaseModel):
    body: str = Field(..., description="Текст сообщения")
    author_type: str = Field("customer", description="Тип автора: customer/agent/ai")
    language: str = Field("ru", description="Язык сообщения, например ru или kk")


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketBase(BaseModel):
    subject: str
    description: str
    channel: str = Field("portal", description="Канал: portal/email/chat/phone")
    language: str = Field("ru", description="Язык обращения, например ru или kk")
    customer_email: Optional[str] = Field(None, description="Email клиента, если есть")
    customer_username: Optional[str] = Field(None, description="Username клиента (например в Telegram)")
    external_user_id: Optional[str] = Field(
        None, description="Внешний идентификатор пользователя или сообщения (например Telegram user id)"
    )
    request_type: Optional[str] = Field(
        None,
        description=(
            "Тип обращения: problem / question / feedback / career / partner / other "
            "(для обратной совместимости также возможны значения difficulty / proposal / job)."
        ),
    )


class TicketCreate(TicketBase):
    pass


class TicketRead(BaseModel):
    id: int
    subject: str
    description: str
    channel: str
    language: str
    customer_email: Optional[str] = None
    customer_username: Optional[str] = None
    category_code: Optional[str] = None
    priority: str
    status: str
    department_name: Optional[str] = None
    auto_closed_by_ai: bool
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TicketDetails(TicketRead):
    messages: List[MessageRead] = []


class ExternalTicketCreate(BaseModel):
    """Создание тикета внешним источником (например, обработчиком почты Outlook).

    Предполагается, что классификация уже выполнена и статусы известны.
    AI‑маршрутизация здесь не вызывается.
    """

    subject: str
    description: str
    channel: str = Field("email", description="Источник, например email")
    language: str = Field("ru", description="Язык обращения")

    customer_email: Optional[str] = Field(None, description="Email клиента, если есть")
    customer_username: Optional[str] = Field(None, description="Username клиента")
    external_user_id: Optional[str] = Field(
        None, description="Внешний идентификатор письма/пользователя"
    )
    request_type: Optional[str] = Field(
        None, description="Тип обращения (если уже определён внешней системой)"
    )

    category_code: Optional[str] = Field(
        None, description="Код категории, определённый внешней системой"
    )
    priority: str = Field("P3", description="Приоритет тикета P1-P4")
    status: str = Field("new", description="Статус тикета (new/in_progress/closed/auto_closed)")
    department_code: Optional[str] = Field(
        None, description="Код департамента, если уже известен"
    )
