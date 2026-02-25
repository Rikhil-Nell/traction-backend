from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.user import User


class OAuthAccount(BaseUUIDModel, table=True):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    user_id: UUID = Field(foreign_key="users.id", index=True)
    provider: str = Field(max_length=50)  # "google", "github", etc.
    provider_user_id: str = Field(max_length=255)  # sub / id from provider
    provider_email: str = Field(max_length=320)

    # Relationships
    user: "User" = Relationship(back_populates="oauth_accounts")
