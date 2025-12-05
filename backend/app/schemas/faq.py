from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class FAQBase(BaseModel):
    question: str = Field(..., description="Вопрос пользователя")
    answer: str = Field(..., description="Ответ/инструкция")
    language: str = Field("ru", description="Язык статьи")
    category_code: Optional[str] = Field(None, description="Код категории, к которой относится статья")
    auto_resolvable: bool = Field(False, description="Можно ли автоматически закрывать тикеты по этой статье")


class FAQCreate(FAQBase):
    pass


class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    language: Optional[str] = None
    category_code: Optional[str] = None
    auto_resolvable: Optional[bool] = None


class FAQRead(FAQBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
