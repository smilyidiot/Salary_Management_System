"""Shared pytest fixtures.

Every test runs against its own fresh in-memory SQLite database (a ``StaticPool`` so the
same connection is reused across the app's threadpool). ``db_session`` is for unit tests
that call services directly; ``client`` is a ``TestClient`` whose ``get_db`` dependency is
overridden to use the same in-memory database. Keeping each test isolated and in-memory
makes the suite fast and deterministic.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db_session(session_factory) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    # The app lifespan auto-seeds an empty database; disable that for tests so they control
    # their own data and never touch the real database.
    original_seed = settings.seed_on_startup
    settings.seed_on_startup = 0
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        settings.seed_on_startup = original_seed
