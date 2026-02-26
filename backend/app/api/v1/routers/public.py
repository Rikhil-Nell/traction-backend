"""Public routes — no authentication required."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectDocument

router = APIRouter(prefix="/public", tags=["public"])


async def _resolve_project(
    username: str,
    project_name: str,
    db: AsyncSession,
) -> tuple[User, Project]:
    """Find a shared project by username and project name.

    - Username lookup is case-insensitive.
    - Project name lookup is case-insensitive; hyphens in the URL are
      replaced with spaces so that URL-safe slugs work.
    - Only projects with status == "shared" are returned.

    Returns (user, project) or raises 404.
    """
    result = await db.execute(
        select(User).where(func.lower(User.username) == username.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Replace hyphens with spaces for URL-safe project name matching
    clean_name = project_name.replace("-", " ")

    result = await db.execute(
        select(Project).where(
            Project.user_id == user.id,
            func.lower(Project.name) == clean_name.lower(),
        )
    )
    project = result.scalar_one_or_none()
    if not project or project.status != "shared":
        raise HTTPException(status_code=404, detail="Project not found")

    return user, project


@router.get("/users/{username}/projects/{project_name}")
async def get_public_project(
    username: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Return a public (shared) project with its documents and owner info."""
    user, project = await _resolve_project(username, project_name, db)

    # Fetch documents for this project
    result = await db.execute(
        select(ProjectDocument).where(ProjectDocument.project_id == project.id)
    )
    documents = result.scalars().all()

    return {
        "project": project,
        "documents": documents,
        "user": {
            "username": user.username,
            "display_name": user.display_name,
        },
    }


@router.get("/users/{username}/projects/{project_name}/llms.txt")
async def get_llms_txt(
    username: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the llms.txt content for a shared project as plain text."""
    _user, project = await _resolve_project(username, project_name, db)
    return PlainTextResponse(content=project.llms_txt or "")


@router.get("/users/{username}/projects/{project_name}/ai.json")
async def get_ai_json(
    username: str,
    project_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the ai.json content for a shared project."""
    _user, project = await _resolve_project(username, project_name, db)
    return JSONResponse(content=project.ai_json or {})
