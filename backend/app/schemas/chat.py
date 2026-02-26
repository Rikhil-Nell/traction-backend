import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatMessageBase(BaseModel):
    role: str
    content: str


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageRead(ChatMessageBase):
    id: UUID
    project_id: UUID
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
