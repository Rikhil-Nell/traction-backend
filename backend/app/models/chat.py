from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.user import User


class Conversation(BaseUUIDModel, table=True):
    __tablename__ = "conversations"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255, default="New Chat")

    # Relationships
    user: "User" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Message.created_at",
        },
    )


class Message(BaseUUIDModel, table=True):
    __tablename__ = "messages"

    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str  # TEXT column (no max_length = TEXT in Postgres)

    # Relationships
    conversation: "Conversation" = Relationship(back_populates="messages")
