import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent_used: str
    sources: list[str]


class HealthResponse(BaseModel):
    status: str
    redis: str
    vectorstore: str
    version: str
