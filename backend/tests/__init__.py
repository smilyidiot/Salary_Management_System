"""Backend test suite.

Unit tests exercise the service layer directly (compensation resolution, analytics math,
seed invariants); API tests drive the FastAPI app through ``TestClient``. All tests run
against a fresh in-memory SQLite database and a small deterministic dataset, so they are
fast and reproducible.
"""
