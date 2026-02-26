import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.controllers import project_controller
from app.core.ai_generators import generate_full_html, generate_document_content
from app.models.project import Project, ProjectDocument
from app.models.user import User


async def generate_deck(
    user: User,
    project_id: uuid.UUID,
    db: AsyncSession,
) -> Project:
    """Generate a full HTML pitch deck from the project's extracted document fields."""
    project = await project_controller.get_project(user, project_id, db)

    project.status = "generating"
    db.add(project)
    await db.commit()

    try:
        # Build all_fields from project documents
        result = await db.execute(
            select(ProjectDocument).where(ProjectDocument.project_id == project.id)
        )
        documents = list(result.scalars().all())
        all_fields = {doc.type: doc.fields or {} for doc in documents}

        full_html = await generate_full_html(project.name, all_fields)

        project.full_html = full_html
        project.status = "draft"

        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    except Exception as e:
        project.status = "draft"
        db.add(project)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Deck generation failed: {str(e)}")


async def generate_documents(
    user: User, 
    project_id: uuid.UUID, 
    doc_types: list[str], 
    db: AsyncSession
) -> list[ProjectDocument]:
    project = await project_controller.get_project(user, project_id, db)
    
    # Create pending documents
    created_docs = []
    for dtype in doc_types:
        doc = ProjectDocument(
            project_id=project.id,
            type=dtype,
            title=dtype.replace("-", " ").title(),
            content="Generating...",
            status="generating"
        )
        db.add(doc)
        created_docs.append(doc)
    
    await db.commit()
    
    # Kick off generation in background or sequentially
    # We'll do it sequentially here for simplicity, but production should use BackgroundTasks
    for doc in created_docs:
        try:
            content = await generate_document_content(
                doc.type, project.name, doc.fields or {}
            )
            doc.content = content
            doc.status = "ready"
            db.add(doc)
            await db.commit()
        except Exception as e:
            doc.status = "error"
            db.add(doc)
            await db.commit()
            
    # return the updated docs
    result = await db.execute(select(ProjectDocument).where(ProjectDocument.project_id == project.id))
    return list(result.scalars().all())
