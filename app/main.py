"""Application entry point for the URL Shortener Service."""

from fastapi import FastAPI

app = FastAPI(
    title="URL Shortener Service",
    description="A small, production-minded URL shortening service built with FastAPI.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return a simple liveness payload."""
    return {"status": "ok"}
