"""API v1 — aggregates all routers under a single prefix."""

from fastapi import APIRouter

from app.api.v1.routers import auth, chat, users, projects, documents, pages, public, share

router = APIRouter()
router.include_router(auth.router)
router.include_router(chat.router)
router.include_router(users.router)
router.include_router(projects.router)
router.include_router(documents.router)
router.include_router(pages.router)
router.include_router(public.router)
router.include_router(share.router)
