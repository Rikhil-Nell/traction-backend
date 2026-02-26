import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.project import ProjectRead, ProjectDocumentRead
from app.schemas.chat import ChatMessageRead


class WorkspacePagePayload(BaseModel):
    project: ProjectRead
    documents: list[ProjectDocumentRead]
    messages: list[ChatMessageRead]


class DocumentPagePayload(BaseModel):
    project: ProjectRead
    documents: list[ProjectDocumentRead]
