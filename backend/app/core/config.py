import secrets
from enum import Enum
from typing import Any

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModeEnum(str, Enum):
    development = "development"
    production = "production"
    testing = "testing"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────
    MODE: ModeEnum = ModeEnum.production
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "TRACTION"

    # ── JWT / Auth ────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Google OAuth ──────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # ── Database ──────────────────────────────────────────────
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "app_db"

    ASYNC_DATABASE_URI: PostgresDsn | str = ""

    @field_validator("ASYNC_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info) -> Any:
        if isinstance(v, str) and v == "":
            data = info.data
            # Skip SSL for local dev (MODE defaults to development)
            mode = data.get("MODE", ModeEnum.development)
            query = "ssl=require" if mode != ModeEnum.development else None
            return PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=data.get("DATABASE_USER"),
                password=data.get("DATABASE_PASSWORD"),
                host=data.get("DATABASE_HOST"),
                port=data.get("DATABASE_PORT"),
                path=data.get("DATABASE_NAME"),
                query=query,
            )
        return v

    # ── OpenAI ────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

settings = Settings()