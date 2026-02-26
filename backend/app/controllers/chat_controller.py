import uuid

from fastapi import HTTPException
from pydantic_ai import Agent, RunContext
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.controllers import project_controller
from app.models.chat_message import ChatMessage
from app.models.user import User


# Define our basic Agent. We will inject the DB session via RunContext.
# This allows the AI to perform structured updates if we define tools for it later.
chat_agent = Agent(
    model="openai:gpt-4o-mini",
    deps_type=AsyncSession,
    system_prompt=(
        "You are an expert AI product designer and ideation assistant. "
        "Your goal is to help the user flesh out their project ideas and structure them into "
        "coherent product documentation. Offer insightful suggestions and ask clarifying questions."
    )
)


async def get_project_messages(
    user: User,
    project_id: uuid.UUID,
    db: AsyncSession,
) -> list[ChatMessage]:
    """Get all messages for a specific project, verifying ownership."""
    project = await project_controller.get_project(user, project_id, db)
    
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project.id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())


async def send_message(
    user: User,
    project_id: uuid.UUID,
    content: str,
    db: AsyncSession,
) -> dict:
    """
    Send a user message, call Pydantic AI, and return the assistant's response.
    Returns a dict containing the new message and tracking updates.
    """
    project = await project_controller.get_project(user, project_id, db)

    # 1. Save user message
    user_message = ChatMessage(
        project_id=project.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    await db.flush()

    # 2. Build history for Pydantic AI (Optional: Pydantic AI can handle history, 
    # but for manual DB parity we often just pass the immediate prompt or format 
    # it into an array of dicts if using the raw provider, but here we'll let Pydantic AI run).
    # For robust history, we'd reconstruct the `pydantic_ai.messages` structures from DB.
    # For v1, we will just send the immediate text with the context, but real usage would look like this:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    
    # Optional: Format history into a string context if not using strict Pydantic AI history arrays
    history_context = "\n".join([f"{m.role}: {m.content}" for m in messages[:-1]])
    
    prompt = f"Previous conversation:\n{history_context}\n\nUser: {content}" if history_context else content

    # 3. Call Pydantic AI
    try:
        # We pass the db session as dependency so tools can use it if added later
        ai_result = await chat_agent.run(prompt, deps=db)
        assistant_content = ai_result.data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Pydantic AI error: {str(e)}")

    # 4. Save assistant message
    assistant_message = ChatMessage(
        project_id=project.id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    # Return structure matching frontend expectations for documentsUpdated
    return {
        "message": assistant_message,
        "documentsUpdated": [] # Placeholder for when the AI uses tools to update documents
    }
