"""Shared FastAPI dependencies."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import ModeEnum, settings
from app.core.security import get_current_user as _get_current_user_from_cookie
from app.db.database import get_db
from app.models.user import User

# Re-export get_db for convenience
__all__ = ["get_db", "get_current_user"]

# Dev user ID — consistent across restarts for dev testing
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def get_or_create_dev_user(db: AsyncSession) -> User:
    """Get or create a development test user."""
    user = await db.get(User, DEV_USER_ID)
    if not user:
        user = User(
            id=DEV_USER_ID,
            email="dev@localhost.test",
            username="dev_user",
            display_name="Development User",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    return user


async def get_current_user(
    user: User = Depends(_get_current_user_from_cookie),
) -> User:
    """
    In production: delegates to cookie-based JWT auth from security module.
    In development: could be extended to auto-create a dev user if needed.
    """
    return user