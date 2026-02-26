"""Chat router — thin HTTP layer, delegates all logic to chat_controller."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.controllers import chat_controller
from app.db.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessageRead, ChatMessageCreate

router = APIRouter(prefix="/projects", tags=["chat"])


@router.get("/{project_id}/messages", response_model=list[ChatMessageRead])
async def get_messages(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a specific project."""
    return await chat_controller.get_project_messages(user, project_id, db)


@router.post("/{project_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    project_id: uuid.UUID,
    payload: ChatMessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Send a message and get an AI response using Pydantic AI.
    Returns a composite object containing the Message and documentsUpdated.
    """
    return await chat_controller.send_message(user, project_id, payload.content, payload.mode, db)
