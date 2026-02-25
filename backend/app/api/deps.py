"""
Shared FastAPI dependencies — single source of truth for DI.

All routers should import get_db and get_current_user from HERE,
not directly from core.security or db.database.
"""

from uuid import UUID

from fastapi import Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import ModeEnum, settings
from app.core.security import (
    get_current_user as _require_auth,
    get_optional_user as _optional_auth,
)
from app.db.database import get_db as _get_db
from app.models.user import User

__all__ = ["get_db", "get_current_user", "get_optional_user"]

# Dev user ID — consistent across restarts for dev testing
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def get_db() -> AsyncSession:
    """Yield an async database session."""
    async for session in _get_db():
        yield session


async def _get_or_create_dev_user(db: AsyncSession) -> User:
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
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Require authentication. In dev mode with no token, auto-creates a dev user
    so you can test protected endpoints without logging in.
    """
    token = request.cookies.get("access_token")

    # Dev bypass: if no token in development mode, use a dev user
    if not token and settings.MODE == ModeEnum.development:
        return await _get_or_create_dev_user(db)

    # Otherwise delegate to the real auth check
    return await _require_auth(request, db)


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Returns user if authenticated, None if not. Never raises.
    Used for public routes where behaviour differs based on login state.
    """
    return await _optional_auth(request, db)