import datetime
import uuid

from pydantic import BaseModel, EmailStr


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    display_name: str | None = None
    avatar_url: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}



