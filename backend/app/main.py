"""FastAPI application entrypoint for SlothSort backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import api_router
from backend.app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Privacy-conscious, local-first AI file organizer backend",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Restrict CORS to configured origins (defaults to local development origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint exposing runtime configuration and status."""
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "default_provider": settings.DEFAULT_PROVIDER,
    }


# Mount all modular REST endpoints under /api
app.include_router(api_router, prefix="/api")
