"""Chat controller — all business logic for conversations and messages."""

import uuid

from fastapi import HTTPException
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.models.chat import Conversation, Message
from app.models.user import User


def _get_openai_client() -> AsyncOpenAI:
    """Create an OpenAI async client."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def create_conversation(
    user: User,
    title: str,
    db: AsyncSession,
) -> Conversation:
    """Create a new conversation for the user."""
    conversation = Conversation(user_id=user.id, title=title)
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


async def list_conversations(
    user: User,
    db: AsyncSession,
) -> list[Conversation]:
    """List all conversations for the user, newest first."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation_messages(
    user: User,
    conversation_id: uuid.UUID,
    db: AsyncSession,
) -> list[Message]:
    """Get all messages for a conversation, verifying ownership."""
    conversation = await _get_user_conversation(user, conversation_id, db)
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def send_message(
    user: User,
    conversation_id: uuid.UUID,
    content: str,
    db: AsyncSession,
) -> Message:
    """
    Send a user message, call OpenAI, and return the assistant's response.

    Steps:
    1. Verify conversation ownership
    2. Save user message
    3. Build message history for OpenAI
    4. Call OpenAI chat completion
    5. Save and return assistant message
    """
    conversation = await _get_user_conversation(user, conversation_id, db)

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    await db.flush()

    # Build history for OpenAI
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    openai_messages = [{"role": m.role, "content": m.content} for m in messages]

    # Call OpenAI
    client = _get_openai_client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages,
        )
        assistant_content = response.choices[0].message.content or ""
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {str(e)}")

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    # Update conversation title on first message
    if len(openai_messages) == 1:
        conversation.title = content[:60] + ("..." if len(content) > 60 else "")

    return assistant_message


async def delete_conversation(
    user: User,
    conversation_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete a conversation and all its messages."""
    conversation = await _get_user_conversation(user, conversation_id, db)
    await db.delete(conversation)


async def _get_user_conversation(
    user: User,
    conversation_id: uuid.UUID,
    db: AsyncSession,
) -> Conversation:
    """Fetch a conversation and verify ownership."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
