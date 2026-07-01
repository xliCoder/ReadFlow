from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    source_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class ChatResponse(BaseModel):
    source_id: str
    question: str
    answer: str
