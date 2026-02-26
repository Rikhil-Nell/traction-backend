from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.project import Project


class ChatMessage(BaseUUIDModel, table=True):
    __tablename__ = "chat_messages"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    role: str = Field(max_length=20)  # "user" or "assistant"
    content: str  # TEXT by default

    # Relationships
    project: "Project" = Relationship(back_populates="messages")
