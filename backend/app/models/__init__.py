# Import all models so SQLModel.metadata registers them for Alembic autogenerate.
from app.models.base import BaseUUIDModel  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.oauth_account import OAuthAccount  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.project import Project, ProjectDocument, ShareLink  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
