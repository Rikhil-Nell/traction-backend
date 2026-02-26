"""
Chat controller with dual-mode (doc / design) logic.

- **doc mode**: drives the AI doc-agent to extract structured fields from
  the user conversation and populate ProjectDocuments.
- **design mode**: triggers full HTML generation, document content expansion,
  llms.txt, and ai.json whenever the extracted fields change.
"""

import uuid
import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel.ext.asyncio.session import AsyncSession

from app.controllers import project_controller
from app.core.ai_generators import (
    doc_agent,
    compute_fields_hash,
    build_extraction_state,
    check_all_complete,
    generate_full_html,
    generate_document_content,
    generate_llms_txt,
    generate_ai_json,
    DOCUMENT_TYPE_TO_ATTR,
    DOCUMENT_TYPE_TITLES,
)
from app.models.chat_message import ChatMessage
from app.models.project import Project, ProjectDocument
from app.models.user import User
from app.schemas.extraction import DOCUMENT_TYPE_FIELDS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1.  get_project_messages
# ---------------------------------------------------------------------------

async def get_project_messages(
    user: User,
    project_id: uuid.UUID,
    db: AsyncSession,
) -> list[ChatMessage]:
    """Return every message for *project_id*, ordered oldest-first.

    Raises 404 if the project does not belong to *user*.
    """
    project = await project_controller.get_project(user, project_id, db)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project.id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# 2.  _ensure_documents_exist
# ---------------------------------------------------------------------------

async def _ensure_documents_exist(
    project: Project,
    db: AsyncSession,
) -> list[ProjectDocument]:
    """Make sure all 9 document types exist for *project*.

    Any missing types are created with empty defaults.  Returns the full
    list of documents for the project.
    """
    result = await db.execute(
        select(ProjectDocument).where(ProjectDocument.project_id == project.id)
    )
    existing_docs = list(result.scalars().all())
    existing_types = {doc.type for doc in existing_docs}

    for doc_type, title in DOCUMENT_TYPE_TITLES.items():
        if doc_type not in existing_types:
            new_doc = ProjectDocument(
                project_id=project.id,
                type=doc_type,
                title=title,
                content="",
                status="pending",
                fields=None,
            )
            db.add(new_doc)
            existing_docs.append(new_doc)

    await db.flush()
    return existing_docs


# ---------------------------------------------------------------------------
# 3.  _handle_doc_mode
# ---------------------------------------------------------------------------

async def _handle_doc_mode(
    project: Project,
    content: str,
    db: AsyncSession,
) -> dict:
    """Process a user message in **doc** mode.

    1. Ensure all documents exist.
    2. Build the current extraction state from document ``fields`` columns.
    3. Load conversation history for context.
    4. Set ``project.prompt`` from the first user message if it is empty.
    5. Call the doc-agent.
    6. Save the assistant reply as a ChatMessage.
    7. Merge extracted fields back into the documents (non-null overwrites,
       null preserves existing values).
    8. Return the standard response dict.
    """
    # --- ensure docs ---
    documents = await _ensure_documents_exist(project, db)

    # --- build current extraction state ---
    current_state = build_extraction_state(documents)

    # --- load message history BEFORE saving the new user message ---
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == project.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = list(result.scalars().all())

    # Build a simple string history for the agent (no pydantic_ai message objects)
    history_lines = [f"{m.role}: {m.content}" for m in messages]
    history_text = "\n".join(history_lines)

    # --- save user message ---
    user_message = ChatMessage(
        project_id=project.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    await db.flush()

    # --- set project.prompt from first user message if still empty ---
    if not project.prompt:
        project.prompt = content
        db.add(project)
        await db.flush()

    # --- call the doc-agent ---
    context = (
        f"Conversation so far:\n{history_text}\n\n"
        f"Current extraction state:\n{json.dumps(current_state, indent=2)}\n\n"
        f"User message: {content}"
    )
    try:
        ai_result = await doc_agent.run(context)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Doc-agent error: {str(e)}")

    # ai_result.output is an ExtractionResult (structured output from pydantic-ai)
    extraction: object = ai_result.output
    assistant_content: str = extraction.response

    # --- save assistant message ---
    assistant_message = ChatMessage(
        project_id=project.id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    # --- merge extracted fields into documents ---
    for doc in documents:
        attr_name = DOCUMENT_TYPE_TO_ATTR.get(doc.type)
        if attr_name is None:
            continue

        # Once a doc is complete, its data is finalized — skip entirely
        existing = doc.fields or {}
        if existing.get("is_complete", False):
            continue

        extracted_section = getattr(extraction, attr_name, None)
        if extracted_section is None:
            continue

        new_fields = extracted_section.model_dump()

        # Build a NEW dict (required: SQLAlchemy JSON columns don't track
        # in-place mutations, so we must assign a different object)
        merged = dict(existing)

        for key, value in new_fields.items():
            if key == "is_complete":
                # Only upgrade False→True, never downgrade
                if value is True:
                    merged["is_complete"] = True
                continue

            if value is None:
                continue

            # Never replace a populated value with an empty one
            old = merged.get(key)
            if old is not None and old != [] and old != "" and old != {}:
                # Only overwrite if new value is also substantive
                if isinstance(value, list) and len(value) == 0:
                    continue
                if isinstance(value, str) and len(value) == 0:
                    continue

            merged[key] = value

        doc.fields = merged
        flag_modified(doc, "fields")

        # Update document status based on is_complete flag
        is_complete = merged.get("is_complete", False)
        doc.status = "ready" if is_complete else "pending"

        db.add(doc)

    await db.flush()

    # --- rebuild extraction state after merge ---
    updated_state = build_extraction_state(documents)
    all_complete = check_all_complete(updated_state)

    return {
        "message": assistant_message,
        "extraction_state": updated_state,
        "all_complete": all_complete,
        "design_generation_triggered": False,
        "project": None,
    }


# ---------------------------------------------------------------------------
# 4.  _handle_design_mode
# ---------------------------------------------------------------------------

async def _handle_design_mode(
    project: Project,
    content: str,
    db: AsyncSession,
) -> dict:
    """Process a user message in **design** mode.

    1. Save the user message.
    2. Compute a hash of the current extraction fields and compare with
       ``project.last_generation_fields_hash``.
    3. If different -> regenerate full_html, document contents, llms_txt,
       ai_json and update the project.
    4. If same -> skip regeneration and return a "no changes" message.
    """
    # --- save user message ---
    user_message = ChatMessage(
        project_id=project.id,
        role="user",
        content=content,
    )
    db.add(user_message)
    await db.flush()

    # --- ensure documents exist ---
    documents = await _ensure_documents_exist(project, db)

    # --- compute fields hash ---
    current_hash = compute_fields_hash([doc.fields for doc in documents])
    generation_needed = current_hash != project.last_generation_fields_hash

    if not generation_needed:
        # No fields changed -> skip regeneration
        assistant_message = ChatMessage(
            project_id=project.id,
            role="assistant",
            content="No changes detected in your project data. The current design is up to date.",
        )
        db.add(assistant_message)
        await db.flush()
        await db.refresh(assistant_message)

        extraction_state = build_extraction_state(documents)
        all_complete = check_all_complete(extraction_state)

        return {
            "message": assistant_message,
            "extraction_state": extraction_state,
            "all_complete": all_complete,
            "design_generation_triggered": False,
            "project": None,
        }

    # --- generation needed ---
    project.status = "generating"
    db.add(project)
    await db.flush()

    try:
        # Build all_fields dict from documents
        all_fields = {doc.type: doc.fields or {} for doc in documents}

        # --- Step 1: Generate full HTML deck ---
        full_html = await generate_full_html(project.name, all_fields)
        project.full_html = full_html
        db.add(project)
        await db.flush()
        logger.info("HTML deck generated for project %s", project.id)

        # --- Step 2: Generate individual document contents (fail gracefully per doc) ---
        for doc in documents:
            try:
                doc_content = await generate_document_content(
                    doc.type, project.name, doc.fields or {}
                )
                doc.content = doc_content
                doc.status = "ready"
                db.add(doc)
            except Exception as doc_err:
                logger.warning(
                    "Failed to generate content for doc %s (project %s): %s",
                    doc.type, project.id, doc_err,
                )
        await db.flush()

        # --- Step 3: Generate llms.txt (non-critical) ---
        try:
            llms_txt = await generate_llms_txt(project.name, all_fields)
            project.llms_txt = llms_txt
        except Exception as llms_err:
            logger.warning("Failed to generate llms.txt for project %s: %s", project.id, llms_err)

        # --- Step 4: Generate ai.json (deterministic, should not fail) ---
        ai_json = await generate_ai_json(project.name, all_fields)
        project.ai_json = ai_json

        # Store hash so next call can skip if nothing changed
        project.last_generation_fields_hash = current_hash
        project.status = "draft"
        db.add(project)
        await db.flush()
        await db.refresh(project)

    except Exception as e:
        logger.exception("Design generation failed for project %s", project.id)
        project.status = "draft"
        db.add(project)
        await db.flush()
        raise HTTPException(
            status_code=502,
            detail=f"Design generation error: {str(e)}",
        )

    # --- save assistant message ---
    assistant_message = ChatMessage(
        project_id=project.id,
        role="assistant",
        content="Design generation complete! Your pitch deck, documents, and AI outputs have been updated.",
    )
    db.add(assistant_message)
    await db.flush()
    await db.refresh(assistant_message)

    extraction_state = build_extraction_state(documents)
    all_complete = check_all_complete(extraction_state)

    return {
        "message": assistant_message,
        "extraction_state": extraction_state,
        "all_complete": all_complete,
        "design_generation_triggered": True,
        "project": {
            "id": str(project.id),
            "user_id": str(project.user_id),
            "name": project.name,
            "prompt": project.prompt,
            "mode": project.mode,
            "status": project.status,
            "slides_html": project.slides_html or [],
            "full_html": project.full_html,
            "thumbnail_url": project.thumbnail_url,
            "llms_txt": project.llms_txt,
            "ai_json": project.ai_json,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        },
    }


# ---------------------------------------------------------------------------
# 5.  send_message  (main entry point)
# ---------------------------------------------------------------------------

async def send_message(
    user: User,
    project_id: uuid.UUID,
    content: str,
    mode: str,
    db: AsyncSession,
) -> dict:
    """Main chat entry point.

    * Verifies project ownership.
    * Updates the project mode if it has changed.
    * Delegates to ``_handle_doc_mode`` or ``_handle_design_mode``.
    """
    # Validate mode before any mutations
    if mode not in ("doc", "design"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{mode}'. Must be 'doc' or 'design'.",
        )

    project = await project_controller.get_project(user, project_id, db)

    # Update mode on the project if caller switched modes
    if project.mode != mode:
        project.mode = mode
        db.add(project)
        await db.flush()

    if mode == "doc":
        return await _handle_doc_mode(project, content, db)

    else:
        # Gate: all 9 docs must be complete before design mode
        documents = await _ensure_documents_exist(project, db)
        extraction_state = build_extraction_state(documents)
        if not check_all_complete(extraction_state):
            incomplete_count = sum(
                1 for info in extraction_state.values()
                if not info.get("is_complete", False)
            )
            incomplete_docs = [
                doc_type for doc_type, info in extraction_state.items()
                if not info.get("is_complete", False)
            ]
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "All 9 documents must be complete before generating designs.",
                    "incomplete_count": incomplete_count,
                    "incomplete_docs": incomplete_docs,
                },
            )
        return await _handle_design_mode(project, content, db)
