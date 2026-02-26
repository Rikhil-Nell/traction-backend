import asyncio
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.controllers import project_controller
from app.core import ai_generators
from app.models.project import Project, ProjectDocument
from app.models.user import User


async def generate_deck(
    user: User, 
    project_id: uuid.UUID, 
    theme: str, 
    db: AsyncSession
) -> Project:
    project = await project_controller.get_project(user, project_id, db)
    
    # In a real app, you might kick this off to Celery or FastStream. 
    # For now, await directly for the API response.
    project.status = "generating"
    db.add(project)
    await db.commit() # Commit to show status to other requests immediately
    
    try:
        html_slides = await ai_generators.generate_deck_html(
            project.name, project.prompt, theme
        )
        
        project.slides_html = html_slides
        project.full_html = "\n".join(html_slides) # simplified compilation
        project.status = "draft"
        
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
        
    except Exception as e:
        project.status = "error"
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
            content = await ai_generators.generate_document_content(
                doc.type, project.name, project.prompt
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
