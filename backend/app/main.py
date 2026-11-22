"""FastAPI application entry point.

API routers are mounted under ``/api``. In a deployed/single-service setup the app also
serves the built React frontend (``settings.static_dir``) with an SPA fallback, and
auto-seeds the database on first boot if it is empty.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import settings
from app.db import SessionLocal, create_all
from app.routers import analytics, employees, meta


def _maybe_seed() -> None:
    """Seed the database if it is empty (e.g. first boot on a fresh deployment)."""
    if settings.seed_on_startup <= 0:
        return
    from app.models import Employee
    from app.seed import generate

    with SessionLocal() as session:
        if session.query(Employee).first() is None:
            generate(session, count=settings.seed_on_startup, seed=42)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_all()
    _maybe_seed()
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


app.include_router(employees.router)
app.include_router(analytics.router)
app.include_router(meta.router)


# --- Serve the built frontend (single-service deployment) -------------------
# Only active when the build output is present (i.e. in the Docker image / production).
# In local dev the Vite server serves the UI, so this block is skipped.
if settings.static_dir and os.path.isdir(settings.static_dir):
    _assets = os.path.join(settings.static_dir, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        # Unmatched /api/* paths should 404, not fall through to index.html.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = os.path.join(settings.static_dir, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        # Any other path is a client-side route — serve the SPA entry point.
        return FileResponse(os.path.join(settings.static_dir, "index.html"))
