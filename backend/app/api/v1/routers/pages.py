import uuid

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.controllers import pages_controller
from app.models.user import User
from app.schemas.pages import WorkspacePagePayload, DocumentPagePayload

router = APIRouter(prefix="/pages", tags=["pages"])


@router.get("/workspace/{project_id}", response_model=WorkspacePagePayload)
async def get_workspace_page(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate project, documents, and messages for the Workspace view."""
    return await pages_controller.get_workspace_page(user, project_id, db)


@router.get("/documents/{project_id}", response_model=DocumentPagePayload)
async def get_document_page(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate project and documents for the Documents view."""
    return await pages_controller.get_document_page(user, project_id, db)
