import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.project import Project, ProjectDocument
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.pages import WorkspacePagePayload, DocumentPagePayload
from app.controllers import project_controller


async def get_workspace_page(user: User, project_id: uuid.UUID, db: AsyncSession) -> WorkspacePagePayload:
    project = await project_controller.get_project(user, project_id, db)
    
    # Get Docs
    docs_result = await db.execute(select(ProjectDocument).where(ProjectDocument.project_id == project_id))
    documents = docs_result.scalars().all()
    
    # Get Messages
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()
    
    return WorkspacePagePayload(
        project=project,
        documents=documents,
        messages=messages
    )


async def get_document_page(user: User, project_id: uuid.UUID, db: AsyncSession) -> DocumentPagePayload:
    project = await project_controller.get_project(user, project_id, db)
    
    docs_result = await db.execute(select(ProjectDocument).where(ProjectDocument.project_id == project_id))
    documents = docs_result.scalars().all()
    
    return DocumentPagePayload(
        project=project,
        documents=documents
    )
