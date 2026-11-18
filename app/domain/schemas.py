from uuid import UUID
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    conversation_id: UUID | None = None

class Source(BaseModel):
    product_id: str
    product_title: str
    price: str | None = None
    rating: str | None = None

class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    sources: list[Source] = Field(default_factory=list)
    request_id: str

class HealthResponse(BaseModel):
    status: str
    version: str = "2.0.0"
