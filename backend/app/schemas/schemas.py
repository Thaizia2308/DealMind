from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _as_utc(v: datetime) -> datetime:
    """SQLite drops timezone info; everything we store is UTC, so make it explicit."""
    return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    industry: str = Field(default="", max_length=200)


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    company: str
    industry: str
    is_demo: bool
    bank_id: str = ""
    created_at: datetime
    interaction_count: int = 0

    _utc = field_validator("created_at")(_as_utc)


class InteractionCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    kind: Literal["note", "call", "meeting", "email", "demo"] = "note"
    occurred_at: Optional[datetime] = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    kind: str
    content: str
    occurred_at: datetime
    retained: bool
    retain_error: str

    _utc = field_validator("occurred_at")(_as_utc)


class MemoryItem(BaseModel):
    text: str
    type: Optional[str] = None


class RecallRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


class RecallOut(BaseModel):
    memories: List[MemoryItem]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class PrepareRequest(BaseModel):
    use_memory: bool = True
    meeting_goal: str = Field(default="", max_length=500)


class FollowupRequest(BaseModel):
    channel: Literal["email", "message"] = "email"
    tone: Literal["professional", "friendly", "concise"] = "professional"
    instructions: str = Field(default="", max_length=500)


class AnswerOut(BaseModel):
    answer: str
    memory_used: bool
    source: Literal["hindsight", "generic-template"]
    memories: List[MemoryItem] = []


class MemoryStatus(BaseModel):
    configured: bool
    reachable: bool
    mode: str
    base_url: Optional[str] = None
    server_version: Optional[str] = None
    error: Optional[str] = None


class DemoStep(BaseModel):
    kind: str
    content: str


class DemoScript(BaseModel):
    name: str
    company: str
    industry: str
    steps: List[DemoStep]
    question: str
