"""Auth controller — all business logic for authentication flows."""

from datetime import datetime, timezone

from fastapi import HTTPException, Response
from sqlalchemy import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.oauth_account import OAuthAccount
from app.models.refresh_token import RefreshToken
from app.models.user import User


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly auth cookies on the response."""
    is_secure = settings.MODE != "development"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Remove auth cookies from the response."""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


# ── OAuth Callback ────────────────────────────────────────────

async def handle_oauth_callback(
    provider: str,
    provider_user_id: str,
    email: str,
    db: AsyncSession,
) -> User:
    """
    Find or create a user from an OAuth callback.

    Account linking logic:
    1. If this exact OAuth account exists → return the linked user
    2. If a user with this email exists → link this provider and return
    3. Otherwise → create a new user + OAuth account
    """
    # 1. Check for existing OAuth link
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
    )
    existing_oauth = result.scalar_one_or_none()
    if existing_oauth:
        user = await db.get(User, existing_oauth.user_id)
        if user:
            return user

    # 2. Check for existing user with same email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Link this OAuth provider to the existing account
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
        )
        db.add(oauth_account)
        await db.flush()
        return user

    # 3. Brand new user
    username = email.split("@")[0]
    # Ensure username uniqueness
    base_username = username
    counter = 1
    while True:
        result = await db.execute(select(User).where(User.username == username))
        if not result.scalar_one_or_none():
            break
        username = f"{base_username}{counter}"
        counter += 1

    user = User(email=email, username=username)
    db.add(user)
    await db.flush()
    await db.refresh(user)

    oauth_account = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=email,
    )
    db.add(oauth_account)
    await db.flush()
    return user


# ── Username / Password Auth ─────────────────────────────────

async def handle_register(
    email: str,
    username: str,
    password: str,
    db: AsyncSession,
) -> User:
    """Register a new user with email + username + password."""
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check username uniqueness
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def handle_login(
    username: str,
    password: str,
    db: AsyncSession,
) -> User:
    """Authenticate a user by username + password."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    return user


# ── Token Issuance ────────────────────────────────────────────

async def issue_tokens(user: User, response: Response, db: AsyncSession) -> None:
    """Create access + refresh tokens and set them as cookies."""
    access_token = create_access_token(user.id)
    refresh_token = await create_refresh_token(user.id, db)
    _set_auth_cookies(response, access_token, refresh_token)


# ── Token Refresh ─────────────────────────────────────────────

async def handle_refresh(
    refresh_token_value: str | None,
    response: Response,
    db: AsyncSession,
) -> User:
    """
    Validate a refresh token, rotate it, and issue a new access token.

    Theft detection: if a revoked token is reused, it means someone stole it
    (the real user already rotated it). In this case, revoke ALL tokens for
    that user as a safety measure — forces re-login on all devices.
    """
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="No refresh token")

    # Hash the incoming raw token to look it up in the DB
    incoming_hash = hash_token(refresh_token_value)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == incoming_hash)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # ── Theft detection ──────────────────────────────────────
    if token_record.is_revoked:
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == token_record.user_id,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True)
        )
        raise HTTPException(
            status_code=401,
            detail="Refresh token reuse detected — all sessions revoked",
        )

    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Rotate: revoke old token
    token_record.is_revoked = True

    # Get user
    user = await db.get(User, token_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Issue new tokens
    await issue_tokens(user, response, db)
    return user


# ── Logout ────────────────────────────────────────────────────

async def handle_logout(
    refresh_token_value: str | None,
    response: Response,
    db: AsyncSession,
) -> None:
    """Revoke the refresh token and clear cookies."""
    if refresh_token_value:
        incoming_hash = hash_token(refresh_token_value)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == incoming_hash)
        )
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.is_revoked = True

    _clear_auth_cookies(response)
