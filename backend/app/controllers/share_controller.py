import secrets
import string
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.controllers import project_controller
from app.core.security import get_password_hash, verify_password
from app.models.project import Project, ProjectDocument, ShareLink
from app.models.user import User


def _generate_slug(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def create_share_link(
    user: User,
    project_id: uuid.UUID,
    is_password_protected: bool,
    password: str | None,
    expires_at: str | None,
    db: AsyncSession,
) -> ShareLink:
    """Create a new share link for a project."""
    project = await project_controller.get_project(user, project_id, db)

    # Avoid duplicate logic for pure public link replacing (simplification)
    # Could check if an identical parameter link already exists here.
    
    password_hash = get_password_hash(password) if is_password_protected and password else None
    
    share_link = ShareLink(
        project_id=project.id,
        slug=_generate_slug(),
        is_password_protected=is_password_protected,
        password_hash=password_hash,
        expires_at=expires_at
    )
    
    db.add(share_link)
    await db.flush()
    await db.refresh(share_link)
    
    # Update project status to shared
    if project.status != "shared":
        project.status = "shared"
        db.add(project)
        await db.flush()
        
    return share_link


async def get_public_project(slug: str, password: str | None, db: AsyncSession) -> dict:
    """
    Fetch a project via a share link slug.
    Validates password if required.
    Returns structurally identical payload to DocumentPagePayload but filters out user_ids.
    """
    # 1. Fetch link
    result = await db.execute(select(ShareLink).where(ShareLink.slug == slug))
    link = result.scalar_one_or_none()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or invalid.")
        
    # 2. Check Password
    if link.is_password_protected:
        if not password:
            raise HTTPException(status_code=401, detail="Password required.")
        if not link.password_hash or not verify_password(password, link.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password.")
            
    # 3. Update Metrics (can be pushed to background task)
    link.view_count += 1
    db.add(link)
    
    # 4. Fetch Project & Documents
    project = await db.get(Project, link.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
        
    docs_result = await db.execute(select(ProjectDocument).where(ProjectDocument.project_id == project.id))
    documents = docs_result.scalars().all()
    
    await db.commit() # Save the view count
    
    return {
        "project": project,
        "documents": documents
    }
