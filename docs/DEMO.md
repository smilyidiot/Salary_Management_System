# Demo script

A ~3-minute click-through for the screen recording. It walks the core HR workflows against
the seeded 10,000-employee dataset.

## Setup (before recording)

1. Seed the database (if not already): from `backend/`, `python -m app.seed`.
2. Start the backend: `uvicorn app.main:app --reload --app-dir backend` (from the repo root,
   with the backend venv active) → http://localhost:8000.
3. Start the frontend: from `frontend/`, `npm run dev` → http://localhost:5173.
4. Open http://localhost:5173 in the browser.

## Script

### 1. The problem it solves (15s)
- Open on the **Dashboard**. Narrate: "ACME's HR team managed 10,000 salaries across
  countries in spreadsheets. This replaces that."

### 2. Pay analytics — "how do we pay people?" (45s)
- Point out the KPI cards: **total headcount (10,000)**, **total annual payroll (~$662M)**,
  **average** and **median** salary.
- **Average salary by country** chart — call out the cost-of-living spread (India low, US
  high), all normalized to USD.
- **Salary distribution** histogram and **by-department** chart.
- Scroll to the **country breakdown table** for exact numbers.

### 3. The directory at scale (45s)
- Go to **Employees**. Note the footer: **10,000 employees**, paginated.
- **Search** a name — watch it narrow instantly (debounced, server-side).
- **Filter** by country and department; **sort** by current salary (USD).
- Mention: searching/filtering/sorting all happen in the database, so the UI only ever loads
  one page.
- Click **Export CSV** — the "replace Excel" escape hatch (respects active filters).

### 4. An employee & their pay history (40s)
- Click a row to open the **detail page**: profile, current salary (USD + local currency),
  manager link, and the **salary-history timeline**.
- Click **Record salary change** — enter a new amount, pick a reason (raise/promotion), save.
- Show the history gain a new row and the **current salary update live** — emphasize that
  history is append-only (an audit trail), not an overwrite.

### 5. Add an employee (30s)
- Click **Add employee**. Fill the form; note currency auto-fills from the country.
- Submit → lands on the new employee's page with their starting compensation recorded.

### 6. Under the hood (15s)
- Briefly show **http://localhost:8000/docs** (FastAPI's auto-generated API explorer).
- Mention the artifacts: `REQUIREMENTS.md`, `ARCHITECTURE.md` (with diagrams), `DECISIONS.md`,
  and the test suite (`pytest` + `npm run test`).

## Talking points to weave in
- Effective-dated compensation is the key modeling decision — it answers *how pay changed
  over time*, not just today's number.
- Analytics are computed in SQL and normalized to USD; verified against an independent
  computation.
- 43 tests; deterministic seed; clean, layered architecture.
