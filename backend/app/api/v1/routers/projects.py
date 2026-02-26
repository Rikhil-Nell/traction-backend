import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.controllers import project_controller, generation_controller
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectDocumentRead
from app.schemas.generation import GenerateDeckRequest, GenerateDocumentsRequest

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project from an initial prompt."""
    return await project_controller.create_project(user, payload.name, payload.prompt, db)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    status: Literal["all", "draft", "generating", "shared"] = Query("all", description="Filter by status"),
    sort: Literal["recent", "name", "status"] = Query("recent", description="Sort order"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the current user."""
    return await project_controller.list_projects(user, db, filter_status=status, sort_by=sort)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific project."""
    return await project_controller.get_project(user, project_id, db)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project's details."""
    return await project_controller.update_project(
        user, project_id, name=payload.name, project_status=payload.status, db=db
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all associated documents/messages."""
    await project_controller.delete_project(user, project_id, db)


@router.get("/{project_id}/documents", response_model=list[ProjectDocumentRead])
async def get_project_documents(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all documents belonging to a specific project."""
    return await project_controller.get_project_documents(user, project_id, db)


@router.post("/{project_id}/generate-deck", response_model=ProjectRead)
async def trigger_deck_generation(
    project_id: uuid.UUID,
    payload: GenerateDeckRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger the AI to build or rebuild the presentation deck."""
    return await generation_controller.generate_deck(user, project_id, payload.theme, db)


@router.post("/{project_id}/generate-documents", response_model=list[ProjectDocumentRead])
async def trigger_document_generation(
    project_id: uuid.UUID,
    payload: GenerateDocumentsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger the AI to build specifically targeted documents."""
    return await generation_controller.generate_documents(user, project_id, payload.document_types, db)
