# Software Requirements Specification (SRS)
## FinTrack — Personal Expense Tracker (V1 / MVP)

**Derived from:** FinTrack_PRD_Final.md
**Document Owner:** Engineering
**Status:** Final v3.0 — Stable V1 / Ready to Build & Deploy

---

## 0. Purpose of This Document

This SRS translates the FinTrack PRD (V1/MVP scope) into a concrete, buildable technical specification: tech stack, architecture, database schema, API contract, folder structure, environment configuration, local run instructions, and deployment plan (Docker + Render + Vercel + Supabase). It is the single source of truth the dev team should code against to ship a stable V1.

Everything in Section 6 (Out-of-Scope) of the PRD — login, multi-currency, recurring expenses, bank sync, notifications, native app — is intentionally **excluded** from this SRS. The schema and architecture are, however, designed so those Phase 2+ features can be added without a rebuild (see §3.7 and §5.7).

---

## 1. Tech Stack (Confirmed + Supporting Tools)

### 1.1 Core Stack (as requested)

| Layer | Technology |
|---|---|
| Backend | **Python 3.12 + FastAPI** |
| Frontend | **Next.js 14+ (App Router, TypeScript)** |
| Database | **PostgreSQL 15+** |

### 1.2 Required Supporting Tools & Technologies

| Concern | Tool | Why |
|---|---|---|
| ORM | **SQLAlchemy 2.0 (async)** | Type-safe models, mature Postgres support, works well with FastAPI |
| Migrations | **Alembic** | Standard migration tool paired with SQLAlchemy; version-controlled schema changes |
| Data Validation / Schemas | **Pydantic v2** | Request/response validation, ships natively with FastAPI |
| DB Driver | **asyncpg** | Async Postgres driver used by SQLAlchemy async engine |
| ASGI Server | **Uvicorn** (+ Gunicorn worker manager in prod) | Runs the FastAPI app |
| Backend Config Mgmt | **pydantic-settings** | Reads `.env` into typed settings, no hardcoded config |
| Backend Testing | **Pytest + pytest-asyncio + httpx.AsyncClient** | Unit + integration tests per PRD §9 Testability |
| Backend Lint/Format | **Ruff + Black** | Consistent code style, fast linting |
| DB Seeding | Custom seed script (`app/db/seed.py`) | Seeds P2 "starter categories" (FR-10) — real DB rows, not hardcoded UI data |
| Frontend State/Data Fetching | **TanStack Query (React Query)** | Server-state caching, loading/error states (PRD requires empty/loading/error states everywhere) |
| Frontend Styling | **Tailwind CSS** | Mobile-first responsive design, design tokens, spacing, typography, breakpoints |
| Frontend Components | **shadcn/ui (Radix primitives)** | Accessible, consistent components for dialogs, menus, dropdowns, forms and overlays |
| UI Animation | **Framer Motion** | Page transitions, modal/drawer animation, list/item transitions and polished micro-interactions |
| 3D / Visual Layer | **React Three Fiber + @react-three/drei** | Lightweight optional 3D visual elements for the dashboard/landing experience; must remain progressive and non-blocking |
| Charts | **Recharts** | Pie/donut + bar/line charts (FR-19, FR-20) |
| Icons | **lucide-react** | Hamburger menu icon, category icons, UI icons |
| Toasts / Feedback | **Sonner** | Non-blocking success/error feedback for CRUD actions |
| HTTP Client (frontend) | **Axios** (wrapped in a typed API client) | Central place to attach base URL from env, handle errors |
| Frontend Forms | **React Hook Form + Zod** | Client-side validation and form state management; backend remains the source of truth |
| Frontend Testing | **Vitest + React Testing Library** | Component/unit tests |
| E2E Testing | **Playwright** | Full user-flow tests (add expense → dashboard updates, per PRD §8 Key User Flows) |
| Date Handling | **date-fns** (frontend), **datetime/zoneinfo** (backend) | Date range filters, "this week/month" logic |
| API Docs | **FastAPI auto Swagger/OpenAPI** (`/docs`, `/openapi.json`) | Contract stays in sync with code |
| Containerization | **Docker + Docker Compose** (compose for local-with-docker option only) | Separate Dockerfiles per PRD requirement |
| CI | **GitHub Actions** | Lint + test on every PR before deploy (PRD §9 Reliability: run→test→deploy each phase) |
| Backend Hosting | **Render** (Web Service) | As requested |
| Frontend Hosting | **Vercel** | As requested |
| Database Hosting | **Supabase (managed Postgres)** | As requested |
| Secrets Mgmt | `.env` (local, gitignored) + Render/Vercel/Supabase dashboard env vars (prod) | No hardcoded config anywhere |

> Note on PRD §9 "Deployment (V1): local or private deployment, no public internet exposure planned for V1, since there is no login/auth layer yet." — You've asked to also prepare Render/Vercel/Supabase deployment. This SRS supports both: run fully local first (no Docker), then optionally deploy. If you deploy publicly before Phase 2 auth exists, treat the deployed URL as private/unlisted and consider adding a minimal shared-secret gate (see §9.4) since there is genuinely no login in V1.

---

## 2. System Architecture (High Level)

```
┌─────────────────────┐        HTTPS/JSON        ┌──────────────────────┐        asyncpg        ┌──────────────────┐
│   Next.js Frontend   │  ───────────────────────▶│   FastAPI Backend    │ ──────────────────────▶│  PostgreSQL (DB)  │
│  (Vercel in prod)    │◀───────────────────────  │   (Render in prod)   │◀────────────────────── │ (Supabase in prod)│
└─────────────────────┘                            └──────────────────────┘                        └──────────────────┘
       │                                                     │
       │ TanStack Query cache                                │ SQLAlchemy (async) + Alembic migrations
       │ Axios API client (NEXT_PUBLIC_API_BASE_URL)          │ Pydantic schemas (request/response contracts)
```

- Frontend never talks to the database directly — everything goes through the FastAPI REST API.
- Backend is stateless (no sessions in V1, since there's no auth) — horizontally scalable later.
- All config (DB URL, API base URL, ports, CORS origins) comes from environment variables — nothing hardcoded.

---

## 3. Database Schema (PostgreSQL)

### 3.1 Entity Overview

- `categories` — user-defined categories (FR-6–FR-10)
- `expenses` — the core expense log (FR-1–FR-5)
- `budgets` — overall + per-category budget goals (FR-26–FR-28)

### 3.2 Table: `categories`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| name | VARCHAR(50) | NOT NULL, UNIQUE (case-insensitive via functional index) |
| is_default | BOOLEAN | NOT NULL, default `false` (marks seeded starter categories, FR-10) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

### 3.3 Table: `expenses`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| title | VARCHAR(50) | NOT NULL |
| category_id | UUID | FK → `categories.id`, `ON DELETE RESTRICT` (see §3.5 for delete rules) |
| amount | NUMERIC(12,2) | NOT NULL, CHECK (`amount > 0`) |
| expense_date | DATE | NOT NULL, CHECK (`expense_date <= CURRENT_DATE`) |
| notes | TEXT | NULL |
| payment_mode | VARCHAR(20) | NULL, CHECK IN (`'cash','card','upi','other'`) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Indexes: `idx_expenses_category_id`, `idx_expenses_expense_date`, `idx_expenses_amount`, and a GIN/trigram index on `title`/`notes` for FR-11 search.

### 3.4 Table: `budgets`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| scope | VARCHAR(10) | NOT NULL, CHECK IN (`'overall','category'`) |
| category_id | UUID | FK → `categories.id`, `ON DELETE CASCADE`, NULL when `scope='overall'`, NOT NULL when `scope='category'` |
| period_month | DATE | NOT NULL — first day of the budget month, e.g. `2026-08-01` (budget defaults to monthly per PRD §11) |
| limit_amount | NUMERIC(12,2) | NOT NULL, CHECK (`limit_amount > 0`) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Unique constraint: `(scope, category_id, period_month)` — one overall budget and one budget per category per month.

Remaining balance and status (`on_track` / `near_limit` / `over_budget`) are **computed at request time** from `SUM(expenses.amount)` for the period — never stored, so it's always live (FR-27).

### 3.5 Category Deletion Rule (FR-8)

`DELETE /api/categories/{id}` behavior:
1. If the category has 0 linked expenses → hard delete.
2. If it has linked expenses → respond `409 Conflict` with the count, unless the request includes `?reassign_to={category_id}` (moves expenses to another category first) or `?force=true` (cascades and deletes the linked expenses, with the frontend showing an explicit warning dialog before sending this).

### 3.6 Database Seeding

Seeding is required for FR-10 (starter categories, so the app isn't empty on first use) and is the only allowed "pre-filled" data in the whole system — everything else must come from real user actions (PRD §7.9 / §9.1, no hardcoded/demo data).

- **Script:** `backend/app/db/seed.py`, run manually (`python -m app.db.seed`), never on every app startup.
- **What it seeds:** A small fixed list of starter categories only — e.g. `Food`, `Transport`, `Rent`, `Utilities`, `Shopping`, `Entertainment`, `Health`, `Other` — each inserted with `is_default = true`.
- **Idempotency:** The script upserts on `name` (case-insensitive) — safe to re-run; it will never duplicate categories or touch `expenses`/`budgets`.
- **No expenses or budgets are ever seeded** — those must always come from a real user action through the API, so the app's empty state (§11) is honest per FR-30.
- **User control:** Seeded categories are ordinary rows once created — the user can rename or delete them like any other category (FR-7/FR-8); `is_default` is only a flag for analytics/UI, not a protection against edits.
- **When it runs:**
  - Local (no Docker): after `alembic upgrade head`, run once manually (§8.3).
  - Docker: not run automatically in the `backend` container's `CMD` (only migrations run automatically) — run it manually the first time via `docker compose exec backend python -m app.db.seed`.
  - Production (Render + Supabase): run once via Render's one-off Shell/Job against the Supabase DB, after the first successful migration — not on every deploy.

### 3.7 Forward-Compatibility Note (for Phase 2 login)

No `users` table exists in V1 (single-user app, PRD §11 assumption). To avoid a rebuild in Phase 2:
- All three tables are created via Alembic migrations (not raw SQL), so a Phase-2 migration can simply `ALTER TABLE ... ADD COLUMN user_id UUID REFERENCES users(id)` and backfill.
- Repository/service layer functions already accept an optional `user_id` parameter internally (unused/`None` in V1) so route logic doesn't change shape later.

### 3.8 ERD (text form)

```
categories (1) ──< (many) expenses
categories (1) ──< (0..many) budgets  [budgets.category_id nullable for scope='overall']
```

---

## 4. ORM & Migrations

- **ORM:** SQLAlchemy 2.0 declarative models in `app/models/`, async session via `asyncpg`.
- **Migrations:** Alembic, initialized in `backend/alembic/`. Every schema change = one Alembic revision, committed to git. No manual DB edits, ever (supports PRD's "no hardcoded data / real data layer" principle).
- Workflow: `alembic revision --autogenerate -m "message"` → review the generated file → `alembic upgrade head`.

---

## 5. API Contract

**Base URL (local):** `http://localhost:8000/api`
**Base URL (prod, example):** `https://fintrack-api.onrender.com/api`
**API Docs:** `GET /docs` (Swagger UI, auto-generated — this is the living contract; the table below is the summary)

All request/response bodies are JSON. All monetary amounts are `NUMERIC(12,2)` serialized as strings or numbers with 2 decimal places, displayed as ₹ on the frontend only (currency symbol is a display concern, not stored in DB).

### 5.1 Health Check

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Returns `{"status": "ok", "db": "connected", "version": "1.0.0"}`. Checks a live DB connection, not just process liveness. Used by Render health checks and local smoke tests. |

### 5.2 Categories

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/categories` | List all categories, each with `expense_count` (FR-9) |
| POST | `/api/categories` | Create category `{ "name": string }` (FR-6) |
| GET | `/api/categories/{id}` | Get one category |
| PUT | `/api/categories/{id}` | Rename category `{ "name": string }` (FR-7) |
| DELETE | `/api/categories/{id}` | Delete category; supports `?reassign_to={id}` or `?force=true` (FR-8, see §3.5) |

### 5.3 Expenses

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/expenses` | Paginated list with query params below (FR-3, FR-11–FR-16) |
| POST | `/api/expenses` | Create expense (FR-2) |
| GET | `/api/expenses/{id}` | Get one expense |
| PUT | `/api/expenses/{id}` | Update any field (FR-4) |
| DELETE | `/api/expenses/{id}` | Delete expense (frontend shows confirm dialog first, FR-5) |

**`GET /api/expenses` query params** (all combinable, per PRD §7.5):

| Param | Type | Example |
|---|---|---|
| `search` | string | matches `title` or `notes` (FR-11) |
| `category_id` | UUID | FR-13 |
| `date_from`, `date_to` | date (`YYYY-MM-DD`) | FR-12 |
| `amount_min`, `amount_max` | decimal | FR-14 |
| `payment_mode` | `cash\|card\|upi\|other` | FR-15 |
| `sort_by` | `amount\|date\|category` | FR-16 |
| `sort_order` | `asc\|desc` | default `desc` |
| `page`, `page_size` | int | default `page=1, page_size=20` |

Response shape:
```json
{
  "items": [ { "id": "...", "title": "...", "category": {"id":"...","name":"..."}, "amount": "1234.00", "expense_date": "2026-08-20", "notes": "...", "payment_mode": "upi", "created_at": "...", "updated_at": "..." } ],
  "page": 1, "page_size": 20, "total_items": 57, "total_pages": 3
}
```

### 5.4 Dashboard / Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard/summary` | Total spend (default: current month, FR-17), recent expenses (FR-18), budget status snapshot (FR-21) |
| GET | `/api/dashboard/charts/category-breakdown` | Data for pie/donut chart — spend grouped by category (FR-19). Params: `date_from`, `date_to` |
| GET | `/api/dashboard/charts/spending-trend` | Data for bar/line chart over time (FR-20). Params: `period=daily\|weekly\|monthly`, `date_from`, `date_to` |
| GET | `/api/dashboard/reports` | Breakdown by period (FR-22). Params: `period=daily\|weekly\|monthly` |
| GET | `/api/dashboard/comparison` | Month-over-month total + % change (FR-23) |
| GET | `/api/dashboard/top-categories` | Ranked categories by spend (FR-24). Params: `limit` (default 5) |
| GET | `/api/dashboard/average-spend` | Average daily/weekly spend (FR-25). Params: `basis=daily\|weekly` |

### 5.5 Budgets

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/budgets` | List budgets. Params: `period_month` (default current month) |
| POST | `/api/budgets` | Create budget `{ "scope": "overall\|category", "category_id": uuid\|null, "period_month": "2026-08-01", "limit_amount": "5000.00" }` (FR-26) |
| GET | `/api/budgets/{id}` | Get one budget |
| PUT | `/api/budgets/{id}` | Update limit amount (FR-26, "update goal anytime") |
| DELETE | `/api/budgets/{id}` | Remove a budget goal |
| GET | `/api/budgets/status` | Live computed status for all active budgets: `spent`, `remaining`, `status: on_track\|near_limit\|over_budget` (FR-21, FR-27, FR-28). Params: `period_month` |

### 5.6 Export (P2 — Nice-to-Have, build only if time permits)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/expenses/export` | Export filtered/full expenses. Params: `format=csv\|pdf\|excel` + same filters as §5.3 (FR-29) |

### 5.7 Standard Error Shape

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "amount must be greater than 0", "field": "amount" } }
```
HTTP status codes used: `400` (validation), `404` (not found), `409` (conflict — e.g. category in use), `422` (Pydantic schema error), `500` (server error).

---

## 6. Folder Structure

### 6.1 Repository Root

```
fintrack/
├── backend/
├── frontend/
├── .gitignore                  # root-level ignores (OS files, IDE files)
├── docker-compose.yml          # optional: run backend+frontend+db together locally via Docker
├── README.md
└── docs/
    └── srs.md                  # this document
```

### 6.2 Backend (FastAPI)

```
backend/
├── app/
│   ├── main.py                  # FastAPI app instance, CORS, router registration
│   ├── config.py                # pydantic-settings — reads .env, no hardcoded values
│   ├── db/
│   │   ├── session.py           # async engine + session factory
│   │   ├── base.py              # declarative base, imports all models for Alembic
│   │   └── seed.py              # seeds starter categories (FR-10) — real DB write, not UI mock data
│   ├── models/
│   │   ├── category.py
│   │   ├── expense.py
│   │   └── budget.py
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── category.py
│   │   ├── expense.py
│   │   ├── budget.py
│   │   └── common.py            # pagination, error shape
│   ├── api/
│   │   ├── deps.py              # shared dependencies (DB session, pagination params)
│   │   └── v1/
│   │       ├── router.py        # aggregates all routers under /api
│   │       ├── health.py
│   │       ├── categories.py
│   │       ├── expenses.py
│   │       ├── budgets.py
│   │       └── dashboard.py
│   ├── services/                # business logic (budget status calc, chart aggregation, search/filter)
│   │   ├── category_service.py
│   │   ├── expense_service.py
│   │   ├── budget_service.py
│   │   └── dashboard_service.py
│   └── core/
│       ├── exceptions.py        # custom exception classes + handlers
│       └── logging.py
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── tests/
│   ├── conftest.py
│   ├── test_categories.py
│   ├── test_expenses.py
│   ├── test_budgets.py
│   └── test_dashboard.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml               # ruff/black config
├── Dockerfile
├── .dockerignore
├── .env                         # local secrets, gitignored
├── .env.example                 # committed template
└── .gitignore
```

### 6.3 Frontend (Next.js)

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                     # redirects to /dashboard
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   ├── expenses/
│   │   │   ├── page.tsx                 # list + search/filter/sort
│   │   │   ├── new/page.tsx             # add expense form
│   │   │   └── [id]/edit/page.tsx       # edit expense form
│   │   └── categories/
│   │       └── page.tsx                 # manage categories (FR-6–FR-9)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── HamburgerMenu.tsx        # FR-1
│   │   │   └── AppShell.tsx
│   │   ├── expenses/
│   │   │   ├── ExpenseForm.tsx
│   │   │   ├── ExpenseList.tsx
│   │   │   ├── ExpenseFilters.tsx
│   │   │   └── DeleteConfirmDialog.tsx  # FR-5
│   │   ├── dashboard/
│   │   │   ├── SummaryCards.tsx
│   │   │   ├── CategoryPieChart.tsx     # FR-19
│   │   │   ├── SpendingTrendChart.tsx   # FR-20
│   │   │   └── BudgetStatusCard.tsx     # FR-21
│   │   ├── budgets/
│   │   │   └── BudgetForm.tsx
│   │   ├── categories/
│   │   │   └── CategoryManager.tsx
│   │   └── ui/                          # shadcn/ui primitives + EmptyState/Loading/ErrorState components
│   │       ├── EmptyState.tsx
│   │       ├── LoadingState.tsx
│   │       └── ErrorState.tsx
│   ├── lib/
│   │   ├── api-client.ts                # axios instance, reads NEXT_PUBLIC_API_BASE_URL
│   │   ├── queries/                     # TanStack Query hooks (useExpenses, useCategories, ...)
│   │   ├── validators/                  # Zod schemas mirroring backend Pydantic rules
│   │   └── utils/
│   │       └── currency.ts              # ₹ formatting, 2-decimal display
│   ├── types/
│   │   ├── expense.ts
│   │   ├── category.ts
│   │   └── budget.ts
│   └── styles/
│       └── globals.css
├── public/
├── tests/
│   ├── unit/
│   └── e2e/                             # Playwright specs
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── Dockerfile
├── .dockerignore
├── .env.local                           # local secrets, gitignored
├── .env.example                         # committed template
└── .gitignore
```

---

## 7. Environment Configuration (No Hardcoding)

### 7.1 `backend/.env.example`

```env
# App
APP_ENV=development
APP_NAME=FinTrack API
API_PORT=8000
LOG_LEVEL=INFO

# Database (local Postgres)
DATABASE_URL=postgresql+asyncpg://fintrack_user:fintrack_pass@localhost:5432/fintrack_db

# CORS — comma-separated frontend origins allowed to call this API
CORS_ORIGINS=http://localhost:3000

# Pagination defaults
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

`backend/.env` is the developer's real local copy of the above (gitignored). In production (Render), the same keys are set as Render environment variables, with `DATABASE_URL` pointing to the Supabase connection string and `CORS_ORIGINS` set to the Vercel frontend URL.

### 7.2 `frontend/.env.example`

```env
# Public — exposed to the browser, must be prefixed NEXT_PUBLIC_
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_NAME=FinTrack
NEXT_PUBLIC_DEFAULT_CURRENCY=INR
```

`frontend/.env.local` is the developer's real local copy (gitignored). In production (Vercel), `NEXT_PUBLIC_API_BASE_URL` is set in the Vercel project's environment variables to the Render backend URL.

---

## 8. Running Locally — Without Docker

### 8.1 Prerequisites
- Python 3.12+, Node.js 20+, PostgreSQL 15+ installed locally.

### 8.2 Database
```bash
createdb fintrack_db
# create fintrack_user with password fintrack_pass and grant privileges on fintrack_db
```

### 8.3 Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                               # then fill in real local values
alembic upgrade head
python -m app.db.seed                               # seeds starter categories (FR-10)
uvicorn app.main:app --reload --port 8000
```
Verify: `GET http://localhost:8000/api/health` → `{"status":"ok",...}`

### 8.4 Frontend
```bash
cd frontend
npm install
cp .env.example .env.local                          # then fill in real local values
npm run dev
```
Visit `http://localhost:3000`.

---

## 9. Dockerized Setup (Separate Dockerfiles, Local + Deploy)

### 9.1 `backend/Dockerfile`
```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}"]
```

### 9.2 `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "start"]
```

### 9.3 `docker-compose.yml` (root — local, optional Docker run)
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: fintrack_user
      POSTGRES_PASSWORD: fintrack_pass
      POSTGRES_DB: fintrack_db
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]

  backend:
    build: ./backend
    env_file: ./backend/.env
    depends_on: [db]
    ports: ["8000:8000"]

  frontend:
    build: ./frontend
    env_file: ./frontend/.env.local
    depends_on: [backend]
    ports: ["3000:3000"]

volumes:
  pgdata:
```

### 9.4 Deployment Targets

| Component | Platform | Notes |
|---|---|---|
| Database | **Supabase** | Create project → copy pooled connection string into `DATABASE_URL` (Render env var). Run `alembic upgrade head` once against it (via Render's shell or a one-off deploy job) plus the seed script. |
| Backend | **Render** (Web Service, Docker deploy using `backend/Dockerfile`) | Set env vars from §7.1 in Render dashboard; health check path = `/api/health`. |
| Frontend | **Vercel** | Deploy `frontend/` as a Next.js project; set `NEXT_PUBLIC_API_BASE_URL` to the Render backend URL in Vercel env vars. |

Since V1 has no auth (PRD §9/§11), if the Render/Vercel URLs become public, consider restricting access temporarily (e.g., Vercel Password Protection, or an `X-Access-Key` header checked by FastAPI middleware) until Phase 2 login ships.

---

## 10. .gitignore Files

### 10.1 Root `.gitignore`
```gitignore
.DS_Store
Thumbs.db
*.log
.vscode/
.idea/
.env
.env.local
```

### 10.2 `backend/.gitignore`
```gitignore
venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
*.egg-info/
.env
!.env.example
.coverage
htmlcov/
```

### 10.3 `frontend/.gitignore`
```gitignore
node_modules/
.next/
out/
.env.local
!.env.example
coverage/
.turbo/
*.tsbuildinfo
```

---

## 11. Frontend Validation — Add / Edit Expense

Validation must run **client-side first** (instant feedback, no round trip) and is always re-checked server-side by Pydantic (§5.3) as the source of truth — the frontend never trusts itself alone.

### 11.1 Field-by-Field Rules

| Field | Required | Client-Side Rule | Error Message Shown | Backend Mirror |
|---|---|---|---|---|
| Title | Yes | Non-empty after trim; max 50 characters | "Title is required" / "Title must be 50 characters or fewer" | `VARCHAR(50) NOT NULL` |
| Category | Yes | Must select an existing category **or** type a new name inline (creates it via `POST /api/categories` on submit) | "Please select or create a category" | FK NOT NULL |
| Amount | Yes | Numeric, strictly greater than 0; max 2 decimal places; reject non-numeric input as you type | "Enter a valid amount greater than 0" | `CHECK (amount > 0)`, `NUMERIC(12,2)` |
| Date | Yes | Valid date; cannot be later than today (compared in local timezone); defaults to today on form open | "Date cannot be in the future" | `CHECK (expense_date <= CURRENT_DATE)` |
| Notes | No | Optional; soft cap ~250 characters to keep list scannable | "Notes must be 250 characters or fewer" | `TEXT`, no DB-level cap (UI-only guard) |
| Payment Mode | No | If provided, must be one of `cash \| card \| upi \| other` (select input, so invalid values aren't possible) | — (constrained by UI control) | `CHECK IN (...)` |

### 11.2 Behavior Rules

- **Validate on blur** for each field, and **re-validate all fields on submit** — the Save button stays disabled while the form is invalid or a request is in flight.
- **Inline errors**, shown directly under the field (not just a toast), so the user knows exactly what to fix.
- **New-category creation inline:** if the user types a category name that doesn't exist, show a "Create '<name>'" option in the category combobox; on submit, create the category first (`POST /api/categories`), then create the expense with the returned `category_id`. If category creation fails (e.g. duplicate name due to a race), surface that error instead of silently proceeding.
- **Duplicate submit guard:** disable the Save button immediately on click to prevent double-submission before the API responds.
- **Server error mapping:** if the backend still rejects the payload (§5.7 error shape), map `error.field` back to the matching form field and show it inline, rather than a generic failure message.
- **Unsaved changes:** if the user navigates away from a dirty Add/Edit form, prompt for confirmation (prevents silent data loss, consistent with PRD's "no losing data by accident" spirit from FR-5).

### 11.3 Implementation

- **Zod schema** (`frontend/src/lib/validators/expense.ts`) defines the rules in §11.1 as a single source of truth for the form; **React Hook Form** wires it to the UI via `zodResolver`.
- Example shape (illustrative, not final code):
```ts
export const expenseSchema = z.object({
  title: z.string().trim().min(1, "Title is required").max(50),
  categoryId: z.string().uuid().optional(),
  newCategoryName: z.string().trim().max(50).optional(),
  amount: z.coerce.number().positive("Enter a valid amount greater than 0"),
  expenseDate: z.coerce.date().max(new Date(), "Date cannot be in the future"),
  notes: z.string().max(250).optional(),
  paymentMode: z.enum(["cash", "card", "upi", "other"]).optional(),
}).refine(data => data.categoryId || data.newCategoryName, {
  message: "Please select or create a category",
  path: ["categoryId"],
});
```
- This same schema (with `expenseDate` optionally allowing the existing value) is reused for the **Edit Expense** form so add/edit validation never drifts apart.

---

## 12. Frontend UI/UX, Responsive Design, Animation & 3D Requirements

### 12.1 Frontend Design Principles

The frontend must be production-quality rather than a basic CRUD interface.

- **Design-first implementation:** build a consistent FinTrack visual system before implementing individual screens.
- **Mobile-first:** every screen must work from small mobile devices through tablets, laptops, desktops and large monitors.
- **Responsive layout:** use Tailwind breakpoints and fluid containers; never depend on fixed desktop widths.
- **No horizontal overflow:** tables/lists/charts/forms must adapt, scroll intentionally where required, or transform into mobile-friendly cards.
- **Consistent design tokens:** centralize typography, spacing, radii, shadows, borders and semantic colors.
- **Accessible UI:** keyboard navigation, focus states, semantic HTML, ARIA where required, sufficient contrast and reduced-motion support.
- **Real data only:** frontend must not contain fake expenses, fake budgets, fake chart datasets or demo rows. Empty states must be driven by actual API responses.
- **Progressive enhancement:** animation and 3D are enhancements; core expense tracking must remain fully usable if animation is disabled or WebGL is unavailable.

### 12.2 Responsive Device Requirements

| Device class | Required behavior |
|---|---|
| Small mobile | Single-column layout, compact navigation, full-width forms, touch-friendly controls |
| Large mobile | Optimized card/list spacing, charts resized without clipping |
| Tablet | Adaptive two-column layouts where useful, drawer/sidebar can expand |
| Laptop | Full dashboard grid, readable tables and charts, comfortable navigation |
| Desktop / large monitor | Centered max-width content, balanced dashboard cards, no stretched UI |
| Touch devices | Minimum practical touch target sizes, no hover-only critical interactions |
| Keyboard-only | All interactive elements reachable and visibly focused |
| Reduced-motion users | Disable/reduce non-essential Framer Motion and 3D animation |

### 12.3 Page-Level UI/UX Requirements

**Dashboard**
- Summary cards for total spend, recent activity and budget status.
- Category breakdown chart and spending trend chart.
- Budget status should be visually understandable without relying on color alone.
- Recent expenses must use real API data.
- Empty dashboard must provide a clear CTA to add the first expense.
- Skeletons must preserve approximate final layout to avoid layout shift.

**Expenses**
- Responsive list/table that becomes cards or a horizontally scrollable data region on small screens.
- Search, filters and sorting must remain usable on mobile.
- Add/Edit forms must have clear labels, helper text and inline validation.
- Destructive actions require confirmation.

**Categories**
- Simple create/rename/delete workflow.
- Show linked expense count before destructive operations.
- Clear conflict/cascade warning.

**Budgets**
- Clear overall/category budget controls.
- Display spent, remaining and status from live backend calculations.
- Make near-limit and over-budget states visually prominent and accessible.

### 12.4 Framer Motion Requirements

Use **Framer Motion** for intentional UI motion, not decoration everywhere.

Required/approved use cases:
- Page/section entrance transitions.
- Drawer and modal open/close animations.
- Expand/collapse interactions.
- List item add/remove/reorder transitions where useful.
- Button press/hover feedback.
- Success state after a successful CRUD action.
- Chart/card entrance animation only when it does not delay useful content.

Rules:
- Keep animations short and subtle.
- Never block API actions behind animation completion.
- Respect `prefers-reduced-motion`.
- Avoid excessive bouncing, spinning or continuous animation.
- Core content must render even if animation fails.

### 12.5 Micro-Interactions

The application should provide small, meaningful feedback for important actions:

- Button hover/tap/focus states.
- Save button loading state while API request is running.
- Success toast after create/update/delete.
- Inline field error animation when validation fails.
- Delete confirmation modal with clear destructive styling.
- Category creation feedback.
- Budget update feedback.
- Skeleton-to-content transition where appropriate.
- Empty-state CTA interaction.
- Copy/share-like feedback only where such functionality exists; do not add fake controls.

Micro-interactions must improve clarity and perceived responsiveness, not distract from financial data.

### 12.6 3D Requirements

3D is optional enhancement and must **never become a dependency for core functionality**.

- Use **React Three Fiber + @react-three/drei** only for a small, optimized visual element where it improves FinTrack's visual identity.
- Prefer one lightweight 3D scene/illustration over multiple 3D scenes.
- Do not render 3D inside critical data tables or forms.
- Provide a static/fallback visual when WebGL is unavailable.
- Lazy-load 3D code so the initial application bundle is not unnecessarily increased.
- Avoid large 3D assets and continuous GPU-heavy animation.
- Respect reduced-motion preferences.
- Mobile devices should receive a lighter 3D treatment or static fallback if performance is insufficient.
- 3D must not affect API calls, database logic, validation or business correctness.

### 12.7 Frontend Validation & UX Consistency

The existing §11 validation remains mandatory.

- **Client-side:** React Hook Form + Zod for immediate feedback.
- **Server-side:** FastAPI + Pydantic validation remains authoritative.
- Validation messages must be human-readable and shown next to the relevant field.
- Backend validation errors must map back to the frontend field whenever `error.field` is available.
- No validation rule may exist only in the frontend for a business-critical constraint.
- Prevent duplicate submissions.
- Warn before losing unsaved form changes.
- Use toast notifications for operation-level feedback and inline messages for field-level errors.

### 12.8 Frontend Performance Requirements

- Use Next.js code splitting and lazy loading for non-critical components.
- Lazy-load the 3D scene and other heavy visual modules.
- Use responsive image assets and avoid oversized static assets.
- Avoid unnecessary client components; prefer Server Components where appropriate and use client components only for interactive UI.
- TanStack Query must handle caching, invalidation and loading/error states for server data.
- Avoid fetching the same resource repeatedly when cached data is valid.
- Charts should render only from API-provided data.
- No blocking animation or 3D initialization before core content is usable.
- Target a smooth experience on typical mobile hardware and avoid avoidable layout shifts.

### 12.9 Frontend Quality Gates

Before V1 release:
- Test all required viewport classes.
- Test keyboard-only navigation for primary flows.
- Test reduced-motion behavior.
- Test with an empty database.
- Test API loading, error and retry states.
- Test slow-network behavior.
- Test WebGL-disabled/unsupported fallback.
- Verify no demo/mock financial data exists in the frontend.
- Verify all CRUD operations use the FastAPI API and real PostgreSQL data.

---

## 13. Existing UI/UX Requirements (Baseline)

- **Layout:** Hamburger menu (FR-1) opening a slide-in drawer with two links — Dashboard, Expenses; Categories reachable from within Expenses or its own drawer item.
- **Responsive:** Mobile-first Tailwind breakpoints; PRD explicitly requires usability on mobile browsers (no native app in V1).
- **States (mandatory on every screen, PRD §6):**
  - Empty state — friendly message + primary CTA ("Add your first expense") when no data exists (ties to FR-30, no fake demo data).
  - Loading state — skeleton loaders for lists/charts, not blank screens.
  - Error state — retry action, human-readable message mapped from the API error shape (§5.7).
- **Forms:** Inline validation matching backend rules (amount > 0, date not in future, title ≤ 50 chars) using Zod — see §11.1 for the full add-expense validation spec.
- **Delete confirmation:** Modal dialog for both expense delete (FR-5) and category delete-with-linked-expenses (FR-8), with an explicit warning when the action cascades.
- **Currency display:** ₹ symbol, 2 decimal places, thousands separators (e.g. ₹1,234.00) — formatting handled by a single `currency.ts` utility, never inline.
- **Charts:** Pie/donut for category breakdown, bar/line for time trend, both with legends and empty-data fallback illustration.
- **Budget status:** Color-coded badge — green (on track), amber (near limit), red (over budget).
- **Accessibility:** Semantic HTML, keyboard-navigable menu/dialogs (via shadcn/ui + Radix), sufficient color contrast for status badges.
- **Design tokens:** Centralize spacing/colors/typography in Tailwind config rather than one-off inline styles, so the look stays consistent as screens are added in later phases.

---

## 14. Non-Functional Requirements Carried Over from PRD

| Requirement | How This SRS Satisfies It |
|---|---|
| Performance — real DB-driven data at any volume | Pagination on `/expenses`, indexed columns (§3.3), aggregation done in SQL not in Python |
| Scalability | Stateless FastAPI service, `user_id`-ready schema (§3.7), containerized for horizontal scaling later |
| Data Integrity — no hardcoded/dummy data | `seed.py` writes only required starter category rows to PostgreSQL; no expenses/budgets/demo transactions are seeded; frontend never ships mock financial data or replaces DB data with static demo data |
| Testability | Pytest (backend) + Vitest/RTL + Playwright (frontend) suites required before merge (CI, §1.2) |
| Reliability — run→test→deploy per phase | GitHub Actions runs lint+tests on every PR; deploy only from a green pipeline |

---

## 15. Definition of Done — Technical Checklist

- [ ] All Alembic migrations applied cleanly from empty DB (`alembic upgrade head`)
- [ ] `GET /api/health` returns `200` with live DB check
- [ ] All endpoints in §5 implemented and covered by Pytest
- [ ] Expense CRUD, category CRUD, budget CRUD fully wired frontend-to-backend
- [ ] Search + at least 2 filters + at least 2 sort options work together on `/expenses`
- [ ] Add/Edit Expense form enforces all §11.1 client-side rules and correctly maps backend validation errors
- [ ] `python -m app.db.seed` populates starter categories idempotently and seeds no expenses/budgets
- [ ] Dashboard renders total spend, recent expenses, 2 charts, and live budget status from real data
- [ ] Empty / loading / error states present on Dashboard, Expenses, Categories, Budget screens
- [ ] Frontend validation passes for all required form constraints and backend validation errors map correctly
- [ ] Responsive behavior verified on mobile, tablet, laptop and desktop viewports with no unintended horizontal overflow
- [ ] Framer Motion page/drawer/form micro-interactions implemented and reduced-motion behavior verified
- [ ] Toast/success/error feedback implemented for major CRUD actions
- [ ] 3D visual is lazy-loaded, lightweight, has a fallback and never blocks core functionality
- [ ] No hardcoded financial/demo data exists in frontend; only required starter categories are seeded into the real database
- [ ] No hardcoded secrets/configuration in frontend or backend — verified via `.env`/`.env.example` review
- [ ] Backend runs locally without Docker; frontend runs locally without Docker
- [ ] `docker compose up` runs the full stack locally
- [ ] Backend deployed to Render, frontend to Vercel, DB on Supabase, end-to-end smoke test passing

---

## 17. Stable V1 Release Gate

The project is considered **Stable V1** only when all of the following are true:

1. PostgreSQL schema can be created from an empty database using Alembic only.
2. Required starter categories can be seeded idempotently using `python -m app.db.seed`.
3. No expenses, budgets, fake chart data or demo transactions are seeded.
4. Frontend contains no hardcoded financial data and reads application data from FastAPI.
5. Client-side Zod validation and backend Pydantic validation both pass.
6. CRUD flows work end-to-end against real PostgreSQL data.
7. Dashboard calculations and charts are based on real API responses.
8. Empty, loading, error and retry states are implemented.
9. Responsive UI works across mobile, tablet, laptop and desktop.
10. Framer Motion interactions are subtle, performant and reduced-motion aware.
11. 3D content is optional, lazy-loaded and has a fallback.
12. Automated backend, frontend and E2E tests pass.
13. Dockerized local environment starts successfully.
14. Render backend health check is green.
15. Vercel frontend communicates successfully with the Render API.
16. Supabase PostgreSQL connectivity and migrations are verified.
17. Production smoke tests cover add → edit → delete expense, category management, search/filter/sort, dashboard updates and budget updates.
18. Secrets are stored only in environment configuration and are not committed to Git.
19. GitHub Actions passes the required lint/test pipeline before release.
20. The deployed V1 is treated as private/unlisted until authentication is introduced in Phase 2, unless an explicit access gate is enabled.

## 16. Build & Launch Order — Step by Step to a Stable, Running V1

Follow this sequence exactly; each stage should be working and tested before moving to the next (PRD §9 Reliability: run → test → deploy per phase).

**Stage 1 — Scaffold**
1. Create the repo with the folder structure in §6.
2. Set up `backend/.env` and `frontend/.env.local` from the `.env.example` templates (§7). Never commit real `.env` files (§10).

**Stage 2 — Database & Backend Core**
3. Install Postgres locally, create `fintrack_db` (§8.2).
4. Write SQLAlchemy models (§3.2–3.4) → generate the first Alembic migration → `alembic upgrade head`.
5. Run `python -m app.db.seed` once (§3.6) to populate starter categories.
6. Build `GET /api/health` first (§5.1) — confirms DB connectivity before anything else is built on top.

**Stage 3 — Backend API**
7. Implement Categories endpoints (§5.2) with the deletion rule (§3.5) → test with Pytest.
8. Implement Expenses endpoints (§5.3), including search/filter/sort query params → test with Pytest.
9. Implement Budgets endpoints (§5.5) with the live status calculation → test with Pytest.
10. Implement Dashboard/report endpoints (§5.4) → test with Pytest.
11. Run the full backend locally (`uvicorn`, §8.3) and manually exercise every endpoint via `/docs`.

**Stage 4 — Frontend Core**
12. Build the API client + TanStack Query hooks (§6.3 `lib/`) pointed at `NEXT_PUBLIC_API_BASE_URL`.
13. Build the Hamburger menu + app shell (FR-1).
14. Build the Expenses screens (list, add, edit) with the full validation from §11, wired to real endpoints — no mock data (FR-30).
15. Build the Categories screen (create/rename/delete with the linked-expense warning, FR-6–FR-9).
16. Build the Dashboard screen: summary cards, both charts, budget status card (§5.4, §13).
17. Add empty/loading/error states everywhere (§13) — verify by testing against an empty DB.

**Stage 5 — Verify End-to-End Locally (No Docker)**
18. Run backend (§8.3) and frontend (§8.4) side by side. Walk every flow in PRD §8: add expense → dashboard updates; search/filter/sort; set a budget → see live remaining balance.
19. Run backend tests (`pytest`) and frontend tests (`vitest`, `playwright`) — all green before proceeding.

**Stage 6 — Dockerize**
20. Add `backend/Dockerfile` and `frontend/Dockerfile` (§9.1–9.2).
21. Run `docker compose up` from the repo root (§9.3) and repeat the Stage 5 walkthrough against the containerized stack.

**Stage 7 — Deploy**
22. Create a Supabase project → get the pooled `DATABASE_URL`.
23. Deploy `backend/` to Render as a Docker web service; set env vars (§7.1) with the Supabase `DATABASE_URL`; confirm `/api/health` is green on Render.
24. Run migrations + seed once against the Supabase DB (via Render's shell, §9.4).
25. Deploy `frontend/` to Vercel; set `NEXT_PUBLIC_API_BASE_URL` to the live Render URL.
26. Smoke-test the deployed app end-to-end; since V1 has no login (§9.4 note), consider a temporary access gate before sharing the URL widely.
27. Check off every item in §15's Definition of Done — that's V1 stable and shippable.
