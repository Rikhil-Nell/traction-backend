import asyncio
import ssl
import sys
import pathlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from app.core.config import settings, ModeEnum
from app.models import *  # noqa: F401, F403 — registers all models with SQLModel.metadata

# Alembic Config object
config = context.config

# Set up loggers from ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = SQLModel.metadata

# Database URL
db_url = str(settings.ASYNC_DATABASE_URI)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode."""
    connect_args = {}

    # Only use SSL for non-development (NeonDB requires it, local Postgres doesn't)
    if settings.MODE != ModeEnum.development:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context

    connectable = create_async_engine(
        db_url,
        echo=True,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())