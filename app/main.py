"""Application entry point for the URL Shortener Service."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.database import init_db
from app.routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="URL Shortener Service",
    description="A small, production-minded URL shortening service built with FastAPI.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return a simple liveness payload."""
    return {"status": "ok"}


# Registered last so /health and /api/* win over the /{code} redirect route.
app.include_router(router)
