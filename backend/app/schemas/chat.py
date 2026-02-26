import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(BaseModel):
    content: str
    mode: Literal["doc", "design"] = "doc"


class ChatMessageRead(ChatMessageBase):
    id: UUID
    project_id: UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    message: ChatMessageRead
    extraction_state: dict
    all_complete: bool
    design_generation_triggered: bool
    project: dict | None = None
