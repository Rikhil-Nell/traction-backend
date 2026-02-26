import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, ProjectDocument
from app.models.user import User


async def create_project(user: User, name: str, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.user_id == user.id, func.lower(Project.name) == name.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have a project with this name.")

    project = Project(
        user_id=user.id,
        name=name,
        prompt="",
        status="draft",
        mode="doc",
        slides_html=[]
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def list_shared_projects(user: User, db: AsyncSession) -> dict:
    query = select(Project).where(Project.user_id == user.id, Project.status == "shared")
    result = await db.execute(query)
    projects = result.scalars().all()
    return {"projects": projects, "count": len(projects)}


async def get_project_by_name(user: User, project_name: str, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.user_id == user.id,
            func.lower(Project.name) == project_name.lower()
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def list_projects(user: User, db: AsyncSession, filter_status: str = "all", sort_by: str = "recent") -> list[Project]:
    query = select(Project).where(Project.user_id == user.id)
    
    if filter_status != "all":
        query = query.where(Project.status == filter_status)
        
    if sort_by == "recent":
        query = query.order_by(Project.created_at.desc())
    elif sort_by == "name":
        query = query.order_by(Project.name.asc())
    elif sort_by == "status":
        query = query.order_by(Project.status.desc())
        
    result = await db.execute(query)
    return result.scalars().all()


async def get_project(user: User, project_id: uuid.UUID, db: AsyncSession) -> Project:
    project = await db.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def update_project(
    user: User, project_id: uuid.UUID, name: str | None, project_status: str | None, mode: str | None, db: AsyncSession
) -> Project:
    project = await get_project(user, project_id, db)
    if name is not None:
        project.name = name
    if project_status is not None:
        project.status = project_status
    if mode is not None:
        project.mode = mode
    
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(user: User, project_id: uuid.UUID, db: AsyncSession) -> None:
    project = await get_project(user, project_id, db)
    await db.delete(project)
    await db.flush()


async def get_project_documents(user: User, project_id: uuid.UUID, db: AsyncSession) -> list[ProjectDocument]:
    project = await get_project(user, project_id, db) # Verify ownership
    result = await db.execute(select(ProjectDocument).where(ProjectDocument.project_id == project.id))
    return result.scalars().all()


async def get_document(user: User, doc_id: uuid.UUID, db: AsyncSession) -> ProjectDocument:
    doc = await db.get(ProjectDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    # Verify owner
    project = await db.get(Project, doc.project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
