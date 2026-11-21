# Requirements — Salary Management

_One-page requirements, written before building. Author: HR-tooling exercise._

## Goal

Give the HR Manager of a ~10,000-employee, multi-country organization a web application
to **manage employee salary data** and **answer questions about how the org pays people**,
replacing the current spreadsheet-based workflow. Success means a non-technical HR Manager
can find any employee, see and update their pay, and read reliable org-wide pay insights —
without touching a spreadsheet.

## Users

A single persona: the **HR Manager**. One trusted internal operator. No external or
employee-self-service users in this version (see Non-goals → Auth).

## Scope & features

1. **Employee directory** — list of all employees with server-side **search** (name /
   employee code / email), **filters** (country, department, employment status), **sorting**,
   and **pagination**. Non-negotiable at 10k rows: the UI never loads the full table at once.
2. **Employee profile** — full record: identity, country, department, job title, level,
   manager, hire date, employment status, and **current salary**.
3. **Compensation as effective-dated history** — salary is not a single editable number. Each
   employee has a timeline of compensation records (amount, currency, pay frequency, effective
   date, reason: hire / raise / promotion / adjustment). "Current salary" is the most recent
   record by effective date. This is the core modeling decision: it answers *how pay changed
   over time*, not just today's figure, and preserves an audit trail.
4. **Create / edit employees** and **record a salary change** (append a new compensation
   record rather than overwriting history).
5. **Pay analytics dashboard** — directly answers "how does the org pay people?":
   - Total headcount and total annualized payroll cost, normalized to a single reporting
     currency (USD) using a seeded FX table.
   - Average and median salary **by country** and **by department**.
   - Salary distribution (histogram / banding).
6. **CSV export** of the currently filtered employee list — a cheap, high-value nod to the
   "replace Excel" pain point (HR can still get a spreadsheet when they genuinely need one).
7. **Seed data** — a deterministic script that generates 10,000 employees with realistic
   multi-country distribution and salary history, so the app is demonstrable and testable.

## Non-goals (deliberately out of scope) and why

| Excluded | Reasoning |
| --- | --- |
| **Authentication / RBAC** | One trusted HR-Manager persona. Auth is orthogonal to the data-modeling and reporting problem being assessed and would add boilerplate without exercising the interesting parts. Called out as the first thing to add before real use. |
| **Payroll run, tax, payslips, benefits/deductions** | A separate, heavily regulated domain. "Salary management" here means managing comp data and reporting on it, not disbursing pay. |
| **Live FX rates** | A static, seeded conversion table keeps the app deterministic, offline, and test-friendly. Live rates are a plug-in replacement later; they don't change the design. |
| **Approval workflows for salary changes** | Direct edits by the trusted HR Manager keep scope on core CRUD + reporting. Multi-step approval is a clear follow-up. |
| **Bulk CSV import UI** | The seed script covers initial load; an import UI is largely file-parsing/validation plumbing that doesn't demonstrate new judgment. Export (the common day-to-day need) is included instead. |
| **Org-chart view, i18n, multi-tenancy, pay-equity/gender analytics** | Not in the problem statement. Each is a reasonable next step and is noted as such rather than half-built. |

## Quality bar

- **Correctness first:** money stored as exact decimals (never floats); analytics computed in
  SQL aggregates, not Python loops, so they stay correct and fast at 10k+ rows.
- **Tested:** meaningful, fast, deterministic unit + API tests on the core logic
  (current-salary resolution, currency normalization, aggregation) rather than blanket coverage.
- **Maintainable:** clear layering (models → services → routers → UI), typed end-to-end.
- **Demonstrable:** one command seeds 10k employees; the app runs locally end-to-end.

## Explicitly not optimizing for

Raw feature count or system complexity. The aim is sound engineering judgment on a realistic
HR problem — a small, correct, well-reasoned system over a large, shallow one.
