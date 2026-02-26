from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.chat_message import ChatMessage


class Project(BaseUUIDModel, table=True):
    __tablename__ = "projects"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=255)
    prompt: str  # TEXT by default
    status: str = Field(default="draft", max_length=50)  # generating, draft, shared
    
    # Store array of strings as JSON
    slides_html: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    full_html: str | None = Field(default=None)
    thumbnail_url: str | None = Field(default=None, max_length=500)

    # Relationships
    user: "User" = Relationship(back_populates="projects")
    documents: list["ProjectDocument"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    messages: list["ChatMessage"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "ChatMessage.created_at"}
    )
    share_links: list["ShareLink"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ProjectDocument(BaseUUIDModel, table=True):
    __tablename__ = "project_documents"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    type: str = Field(max_length=100) # product-description, etc.
    title: str = Field(max_length=255)
    content: str
    status: str = Field(default="pending", max_length=50) # generating, ready, error, pending

    # Relationships
    project: "Project" = Relationship(back_populates="documents")


class ShareLink(BaseUUIDModel, table=True):
    __tablename__ = "share_links"

    project_id: UUID = Field(foreign_key="projects.id", index=True)
    slug: str = Field(max_length=255, unique=True, index=True)
    is_password_protected: bool = Field(default=False)
    password_hash: str | None = Field(default=None, max_length=255)
    expires_at: str | None = Field(default=None) # Or datetime, but frontend expects ISO string or null
    view_count: int = Field(default=0)

    # Relationships
    project: "Project" = Relationship(back_populates="share_links")
