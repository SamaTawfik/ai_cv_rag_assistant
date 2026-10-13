
from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="The question to ask the AI CV assistant.",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be empty.")
        return value


class SourceItem(BaseModel):
    file_name: str
    page_number: int | None = None
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)


class UploadResponse(BaseModel):
    file_name: str
    pages_loaded: int
    chunks_stored: int
    status: str


class HealthResponse(BaseModel):
    status: str

class EmbeddingRequest(BaseModel):
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Text cannot be empty.")
        return value


class EmbeddingResponse(BaseModel):
    dimensions: int
    embedding: list[float]