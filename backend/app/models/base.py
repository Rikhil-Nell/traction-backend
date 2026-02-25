from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlmodel import SQLModel, Field


def utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def created_at_field() -> Any:
    """Factory for created_at field to avoid shared Column objects."""
    return Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )


def updated_at_field() -> Any:
    """Factory for updated_at field to avoid shared Column objects."""
    return Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": func.now(), "nullable": True},
    )


class BaseUUIDModel(SQLModel):
    """Base model with UUID primary key and timestamps."""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
    )

    created_at: datetime = created_at_field()
    updated_at: datetime | None = updated_at_field()
