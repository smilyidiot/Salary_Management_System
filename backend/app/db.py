"""Database engine, session factory, and FastAPI session dependency.

A single SQLite file backs the app. The declarative ``Base`` is defined here and
imported by the models module.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# ``check_same_thread=False`` is required so the SQLite connection can be used across
# FastAPI's threadpool. It is safe here because each request gets its own session.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a request-scoped session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Create tables for every registered model. Safe to call repeatedly."""
    # Import models for their side effect of registering with ``Base.metadata``.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
