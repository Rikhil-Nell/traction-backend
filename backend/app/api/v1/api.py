"""API v1 — aggregates all routers under a single prefix."""

from fastapi import APIRouter

from app.api.v1.routers import auth, chat, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(chat.router)
router.include_router(users.router)
