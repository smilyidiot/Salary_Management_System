# Design decisions & trade-offs

Short, ADR-style notes on the choices that shaped this project and why. The theme
throughout: prefer a small, correct, well-reasoned system over a large, shallow one.

---

## 1. Compensation as effective-dated history, not a single salary field

**Decision:** Salary lives in a `compensation_records` table (amount, currency, frequency,
effective date, reason). "Current salary" is derived as the record with the latest
`effective_from`. Changes are **appended**, never updated.

**Why:** The HR Manager needs to answer questions about pay *over time* and keep an audit
trail — "when did this raise happen", "what was the starting salary". A single mutable
column throws that history away and tends to drift out of sync with reality.

**Trade-off:** Every read of "current salary" is a resolution step (a join/sort), not a
column read. Addressed with an index on `(employee_id, effective_from)` and a single
window-function join on the list/analytics paths (see #4).

## 2. Aggregations in SQL, not Python loops

**Decision:** Counts, averages, and totals are computed with SQL `GROUP BY`; only medians
are computed in Python.

**Why:** At 10k+ employees, pulling every row into Python to aggregate is wasteful and
scales poorly. The database is built for this.

**Trade-off:** SQLite has no native median function, so medians are computed from a single
ordered pull per dimension. This is a pragmatic exception, documented in
`services/analytics.py`. It would move into SQL on Postgres (`percentile_cont`).

## 3. Static, seeded FX table instead of live exchange rates

**Decision:** A fixed currency→USD table in `app/reference.py` normalizes multi-country pay
to USD for reporting.

**Why:** Keeps the app deterministic, offline, and test-friendly, and avoids an external
dependency for what is a reporting convenience. Live rates are a drop-in replacement that
doesn't change the design.

**Trade-off:** Reported USD figures aren't real-time. Acceptable for a pay-analysis tool;
the conversion point is isolated behind one function (`to_usd`).

## 4. Current salary resolved with one window-function join (no N+1)

**Decision:** The directory list and analytics use a shared subquery
(`services/salary_sql.py`) that selects the most recent compensation record per employee via
`ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY effective_from DESC)`, then computes
the USD figure in SQL.

**Why:** Resolving current salary per-employee would be an N+1 query storm on a 10k list.
One join keeps paging and sorting (including sort-by-salary) in the database.

**Trade-off:** The SQL is more involved than a naive query, but it is written once and
reused, so the list and the dashboard can never disagree on "current salary in USD".

## 5. Money as `Decimal`, serialized as a string

**Decision:** Amounts are stored as `Numeric(14,2)` and handled as Python `Decimal`; the API
serializes them as JSON **strings**, and the frontend formats them for display.

**Why:** Floats can't represent currency exactly. Keeping money as decimals end-to-end (and
as strings over the wire) avoids rounding surprises.

**Trade-off:** The frontend must parse strings to numbers for charts. A small, explicit cost
for correctness. (A seed bug where in-memory and DB representations differed —
`50600` vs `50600.00` — was caught by the determinism test and fixed by quantizing to cents.)

## 6. SQLite now, Postgres-ready

**Decision:** SQLite via SQLAlchemy 2.0, selected through a `DATABASE_URL` setting.

**Why:** Zero-setup, self-contained deliverable. The ORM and the aggregation approach
(window functions, `GROUP BY`) are standard SQL, so moving to Postgres is a URL change plus
a median tweak — not a rewrite.

## 7. Mantine component library + hand-written types

**Decision:** Mantine for UI (data tables, forms, modals, notifications) and **hand-written**
TypeScript types mirroring the backend schemas, rather than an OpenAPI code generator.

**Why:** Mantine lets effort go into product logic instead of building UI primitives. For a
project this size, a handful of hand-written types is simpler than wiring up a codegen
pipeline, and keeps the contract legible in one file (`api/types.ts`).

**Trade-off:** Types can drift from the backend if a schema changes. At this scale the risk
is low and visible; a larger project would adopt generated types.

## 8. No authentication (scope)

**Decision:** A single implicit HR-Manager persona; no auth/RBAC.

**Why:** Auth is orthogonal to the data-modeling and reporting problem being assessed and
would add boilerplate without exercising the interesting parts. It's the first thing to add
before real use (see `REQUIREMENTS.md`).

## 9. Single deployable service in production

**Decision:** In dev, two servers (Vite proxies `/api` to FastAPI). In production, FastAPI
serves the built React assets, so the app ships as **one** process.

**Why:** Simplest possible deploy (one free-tier service, no separate frontend host, no CORS
surface). Decided up front so the frontend's API base path was correct from the start.

## 10. Meaningful tests, not blanket coverage

**Decision:** 43 tests total. Backend: service-layer unit tests (salary resolution, USD
conversion, aggregation math), API tests via `TestClient`, and seed invariant/determinism
tests. Frontend: formatters, the list's filter/refetch behavior, and the salary-change
form's validation.

**Why:** Fast, deterministic tests on the logic that actually carries risk (money math,
current-salary resolution, validation) are worth more than coverage numbers. Backend tests
run against a fresh in-memory SQLite with a small deterministic dataset so exact values can
be asserted.

---

## Performance considerations

- **Server-side pagination + filtering** — the directory endpoint returns one page; the
  client never materializes 10k rows.
- **SQL aggregation** — analytics scale with the database, not with Python.
- **Targeted indexes** — on every filter/group column (`country`, `department`,
  `employment_status`) and the history-resolution key `(employee_id, effective_from)`.
- **No N+1** — current salary resolved with a single windowed join (#4).
- **Deterministic seed** — fixed RNG seed makes data, tests, and demos reproducible.
- **Single React instance** — `resolve.dedupe` in `vite.config.ts` prevents a duplicate-React
  "invalid hook call" class of bug.
