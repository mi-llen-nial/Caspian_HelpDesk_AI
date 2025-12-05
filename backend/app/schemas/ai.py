from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    category_code: str = Field(..., description="Код категории")
    department_code: str = Field(..., description="Код департамента")
    priority: str = Field(..., description="Приоритет: P1-P4")
    language: str = Field(..., description="Определённый язык обращения")
    auto_resolvable: bool = Field(False, description="Можно ли автоматически решить")
    confidence: float = Field(..., description="Уверенность модели 0-1")


class SummaryResult(BaseModel):
    summary: str


class AnswerSuggestion(BaseModel):
    answer: str
    answer_language: str


class ReplySuggestions(BaseModel):
    suggestions: list[str]
