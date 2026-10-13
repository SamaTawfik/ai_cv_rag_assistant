from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description="The question to ask the AI CV assistant.",
    )


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
