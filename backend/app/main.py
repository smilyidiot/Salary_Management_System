"""FastAPI application entry point.

Routers are mounted under ``/api``. During the scaffold phase only a health check
exists; employee and analytics routers are added in later steps.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.db import create_all


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Ensure tables exist on boot. Seeding is a separate explicit step (python -m app.seed).
    create_all()
    yield


app = FastAPI(
    title="Salary Management API",
    version=__version__,
    description="Manage employee salary data for a multi-country organization.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe used by the frontend and by deployment health checks."""
    return {"status": "ok", "version": __version__}
