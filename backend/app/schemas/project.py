import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    prompt: str
    status: str = "draft"
    slides_html: list[str] = []
    full_html: str | None = None
    thumbnail_url: str | None = None


class ProjectCreate(BaseModel):
    name: str
    prompt: str


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: str | None = None  # "draft" or "shared"


class ProjectRead(ProjectBase):
    id: UUID
    user_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    model_config = {"from_attributes": True}


class ProjectDocumentBase(BaseModel):
    type: str # 'product-description', 'timeline', etc.
    title: str
    content: str
    status: str = "pending"


class ProjectDocumentRead(ProjectDocumentBase):
    id: UUID
    project_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime | None

    model_config = {"from_attributes": True}
    

class ShareLinkBase(BaseModel):
    slug: str
    is_password_protected: bool = False
    expires_at: str | None = None


class ShareLinkRead(ShareLinkBase):
    id: UUID
    project_id: UUID
    view_count: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ShareLinkCreate(BaseModel):
    is_password_protected: bool = False
    password: str | None = None
    expires_at: str | None = None
