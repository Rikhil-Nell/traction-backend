from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.api import router
from app.core.config import settings
from app.db.database import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: warm up DB pool. Shutdown: dispose engine."""
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────

# SessionMiddleware — required for Authlib OAuth state storage
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# CORS
ALLOWED_ORIGINS = [
    # Development
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # Production
    "https://nebularblazar.com",
    "https://www.nebularblazar.com",
    "https://remiscus.me",
    "https://www.remiscus.me",
    "https://app.remiscus.me",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────

app.include_router(router, prefix=settings.API_V1_STR)


# ── Health / Root ─────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Welcome to the Traction API"}


@app.get("/db_check")
async def db_check(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }
