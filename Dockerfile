# syntax=docker/dockerfile:1
# Single-image build: compile the React frontend, then serve it (and the API) from FastAPI.

# --- Stage 1: build the React frontend ---
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python backend that serves the API and the built frontend ---
FROM python:3.12-slim AS app
WORKDIR /app

# Install backend (runtime dependencies only — no dev extras).
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir .

# Copy the built frontend into the directory the API serves from.
COPY --from=frontend /frontend/dist ./static

ENV SALARY_STATIC_DIR=/app/static \
    SALARY_DATABASE_URL=sqlite:////app/salary.db \
    PYTHONUNBUFFERED=1

# Bake a seeded database into the image so the app starts instantly with data.
RUN python -m app.seed

EXPOSE 8000
# Render and most PaaS inject $PORT; default to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
