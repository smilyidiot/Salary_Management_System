"""Application configuration.

Settings are read from the environment (and an optional ``.env`` file) so the same
code runs locally and in a deployed environment without edits.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SALARY_", extra="ignore")

    # SQLite database URL. Defaults to a file in the backend directory.
    database_url: str = f"sqlite:///{(BASE_DIR / 'salary.db').as_posix()}"

    # Permit the Vite dev server to call the API during local development.
    cors_origins: list[str] = ["http://localhost:5173"]

    # Directory of the built frontend (dist). When it exists, the API also serves the SPA,
    # so the whole app runs as a single service in production. Empty/missing in dev.
    static_dir: str = str(BASE_DIR / "static")

    # Auto-seed this many employees on startup if the database is empty (e.g. first boot in
    # a deployed environment). Set to 0 to disable.
    seed_on_startup: int = 10_000


settings = Settings()
