# AI usage & prompts

This project was built with an agentic AI coding tool (Claude Code). This document records
how AI was used intentionally — the workflow, the guardrails, and representative prompts —
so the thinking behind the solution is transparent.

## Working style

The guiding principle was **AI as an accelerator under human control**, not an autopilot.
Concretely:

1. **Plan before building.** The assessment brief was read first, then a one-page
   requirements doc and an architecture doc (with diagrams) were written *before* any code.
   The implementation was broken into a numbered sequence of small steps.
2. **Incremental, verified steps.** Each step produced one logical unit of work, which was
   **verified before moving on** — backend endpoints exercised via `TestClient`/Swagger,
   analytics cross-checked against an independent pure-Python computation, and frontend pages
   driven in a real browser (clicking through flows, checking the console for errors).
3. **Human-reviewed commits.** Every step was reviewed and committed by hand, so the commit
   history reflects a real, inspectable development process rather than one giant dump.
4. **Correctness over volume.** When a test surfaced a subtle issue (e.g. a money
   representation mismatch in the seed), the root cause was fixed rather than the test
   loosened.

## Representative prompts & instructions

These paraphrase the direction given to the AI at each phase.

### Framing / planning
> "I have a take-home assessment to build salary-management software for a 10,000-employee,
> multi-country org. Read the brief. Help me understand how to approach it well — scope it,
> decide the architecture, and lay out an incremental plan before writing any code."

> "Stack: Python/FastAPI backend, React + Vite frontend, SQLite. Build locally first, deploy
> later. Add artifacts that show thinking — an architecture diagram with tech details, and a
> few more you'd suggest."

### Guardrails given throughout
> "Build one step at a time. After each step, stop and let me review and commit it myself —
> don't run git commits."

> "Add a short docstring to each file explaining its purpose."

### Modeling / backend
> "Model salary as effective-dated history, not a single field, so we can answer how pay
> changes over time. Store money as exact decimals. Make the 10k seed deterministic."

> "Compute analytics (headcount, avg/median, total payroll) in SQL `GROUP BY`, not Python
> loops, and normalize currencies to USD. Cross-check the results against an independent
> computation before trusting them."

### Frontend
> "Employee directory must work at 10k rows — server-side search, filter, sort, pagination.
> Build the detail page with a salary-history timeline and a record-a-raise flow. Then a
> dashboard that answers 'how does the org pay people?'"

> "Verify each page in a real browser — click through the flows and check the console is
> clean — not just that it type-checks."

### Testing
> "Write meaningful, fast, deterministic tests on the core logic — current-salary resolution,
> currency conversion, aggregation math, and form validation — not blanket coverage."

## Where AI helped most

- Scaffolding boilerplate (project setup, typed API client, Mantine forms) quickly.
- Generating a realistic deterministic dataset and the aggregation SQL.
- Catching its own mistakes via tests and browser verification (the determinism test
  surfaced a real money-formatting bug).

## Where human judgment drove

- The **product scope** and explicit non-goals.
- The **core data model** (effective-dated compensation) and the decision to keep
  aggregation in SQL.
- The **incremental, review-and-commit workflow** and the quality bar ("correctness first").
