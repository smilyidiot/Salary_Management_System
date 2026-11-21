# Salary Management

Web-based salary management software for an organization with ~10,000 employees across
multiple countries. It replaces spreadsheet-based HR workflows and lets an HR Manager
manage employee salary data and answer questions about how the org pays people.

Built as a take-home assessment. See [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) for
scope and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design.

## Tech stack

| Layer    | Choice                                   |
| -------- | ---------------------------------------- |
| Backend  | Python · FastAPI · SQLAlchemy 2.0        |
| Database | SQLite (relational)                      |
| Frontend | React · Vite · TypeScript · Mantine      |
| Tests    | pytest (backend) · Vitest + RTL (frontend) |

## Project layout

```
backend/    FastAPI app, models, services, seed script, tests
frontend/   React + Vite single-page app
docs/        requirements, architecture, decisions, prompts, demo script
```

## Quick start

> Prerequisites: Python 3.10+, Node 18+.

### Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -e ".[dev]"
python -m app.seed          # seed 10,000 employees
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

### Tests

```bash
cd backend && pytest
cd frontend && npm run test
```

_More detailed instructions are filled in as the project is built out._
