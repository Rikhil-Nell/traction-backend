from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.oauth_account import OAuthAccount
    from app.models.refresh_token import RefreshToken


class User(BaseUUIDModel, table=True):
    __tablename__ = "users"

    email: str = Field(max_length=320, unique=True, index=True)
    username: str = Field(max_length=50, unique=True, index=True)
    display_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)

    # Relationships
    oauth_accounts: list["OAuthAccount"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    projects: list["Project"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
