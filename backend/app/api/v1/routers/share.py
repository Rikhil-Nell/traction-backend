import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.controllers import share_controller
from app.models.user import User
from app.schemas.project import ShareLinkRead, ShareLinkCreate
from app.schemas.pages import DocumentPagePayload

router = APIRouter(prefix="/share", tags=["share"])


@router.post("/projects/{project_id}", response_model=ShareLinkRead)
async def create_share_link(
    project_id: uuid.UUID,
    payload: ShareLinkCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new public share link for a project."""
    if payload.is_password_protected and not payload.password:
        raise HTTPException(status_code=400, detail="Password is required when is_password_protected is true")
        
    return await share_controller.create_share_link(
        user, project_id, payload.is_password_protected, payload.password, payload.expires_at, db
    )


@router.get("/{slug}", response_model=DocumentPagePayload)
async def get_shared_project(
    slug: str,
    x_share_password: str | None = Header(None, alias="X-Share-Password"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific project via a public share link.
    This route is PUBLIC and does not require a valid access token, but might require a password header.
    """
    return await share_controller.get_public_project(slug, x_share_password, db)
