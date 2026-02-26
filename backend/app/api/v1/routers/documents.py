import uuid

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.controllers import project_controller
from app.models.user import User
from app.schemas.project import ProjectDocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{doc_id}", response_model=ProjectDocumentRead)
async def get_document(
    doc_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    return await project_controller.get_document(user, doc_id, db)
