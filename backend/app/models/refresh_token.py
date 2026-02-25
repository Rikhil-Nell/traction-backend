from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime
from sqlmodel import Field, Relationship

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(BaseUUIDModel, table=True):
    __tablename__ = "refresh_tokens"

    user_id: UUID = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(max_length=64, unique=True, index=True)
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))
    is_revoked: bool = Field(default=False)

    # Relationships
    user: "User" = Relationship(back_populates="refresh_tokens")
