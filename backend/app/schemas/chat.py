import datetime
import uuid

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "New Chat"


class ConversationRead(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
