# Software Requirements Specification (SRS)
## FinTrack — Personal Expense Tracker (with Secure Authentication & Data Isolation)

**Derived from:** FinTrack_PRD.md
**Document Owner:** Engineering
**Status:** Final v4.0 — Production-Ready Authentication & Strict Data Isolation

---

## 0. Purpose of This Document

This Software Requirements Specification (SRS) translates the FinTrack PRD into a concrete, buildable technical specification: tech stack, architecture, database schema, API contract, folder structure, environment configuration, local run instructions, deployment plan, and comprehensive security/authentication mechanisms.

This release introduces **secure, production-ready JWT authentication, Google OAuth 2.0 / OpenID Connect sign-in, and strict user-level data isolation** across all application resources (expenses, categories, budgets, and analytics dashboards) without changing the core FastAPI + Next.js + PostgreSQL architecture.

---

## 1. Tech Stack & Supporting Tools

### 1.1 Core Stack

| Layer | Technology |
|---|---|
| Backend | **Python 3.12 + FastAPI** |
| Frontend | **Next.js 14+ (App Router, TypeScript)** |
| Database | **PostgreSQL 15+** |

### 1.2 Supporting Tools & Libraries

| Concern | Tool / Library | Purpose & Rationale |
|---|---|---|
| ORM | **SQLAlchemy 2.0 (async)** | Type-safe async models and query composition |
| Migrations | **Alembic** | Version-controlled schema migrations for `users`, `refresh_tokens`, and user-scoped tables |
| Data Validation / Schemas | **Pydantic v2** | Strict request/response validation contracts |
| DB Driver | **asyncpg** | High-performance async Postgres driver |
| Password Hashing | **pwdlib / passlib (Argon2 / BCrypt)** | Secure salted password hashing; never store plaintext passwords |
| JWT Engine | **python-jose / PyJWT** | Creation and cryptographic validation of short-lived JWT access tokens |
| OAuth & Social Auth | **authlib / httpx / google-auth** | Backend verification of Google OAuth 2.0 / OIDC ID tokens |
| AI Recommendations & LLM | **google-generativeai (Gemini 1.5 Flash)** | Powers automated Monthly Financial Health Summary and cost-saving advice |
| Rate Limiting | **slowapi (Limiter)** | Protects `/api/auth/login`, `/api/auth/register`, and `/api/auth/forgot-password` against brute-force attacks |
| Email Dispatch | **fastapi-mail / SMTP client** | Dispatches password-reset tokens and verification emails |
| Frontend Auth & Session | **React Context + TanStack Query** | Centralized auth state, automatic access token renewal, user profile synchronization |
| HTTP Client (Frontend) | **Axios (with interceptors)** | Attaches `Authorization: Bearer <token>` and intercepts `401 Unauthorized` for automatic refresh token rotation |
| Social Login UI | **@react-oauth/google** | Google Identity Services / One-Tap & standard Sign-In button integration |
| Frontend Styling | **Tailwind CSS** | Design tokens, responsive layout, glassmorphic dark-mode theme |
| UI Animation | **Framer Motion** | Polished transitions for auth dialogs, forms, and feedback micro-interactions |
| Testing Suites | **Pytest + pytest-asyncio + httpx.AsyncClient** | Backend unit, integration, and security isolation tests |
| Frontend & E2E Testing | **Vitest + RTL + Playwright** | Frontend component validation and end-to-end user journeys |

---

## 2. System Architecture & Security Boundary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Next.js Frontend (Vercel)                        │
│  - App Router, AuthContext, Axios Client (withCredentials: true)            │
│  - Stores Access Token in Memory (Short-Lived: ~15 min)                     │
│  - Stores Refresh Token in HttpOnly, Secure, SameSite=Lax Cookie (~14 days) │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
               HTTPS / JSON        │  Authorization: Bearer <Access Token>
               (Credentials: true) │  Cookie: refresh_token=<Token>
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend (Render)                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Security & Auth Layer (deps.py)                                       │  │
│  │  - Validates JWT signature, expiration & claims                       │  │
│  │  - Extracts authenticated user_id from Security Context              │  │
│  │  - Enforces Data Isolation: query WHERE user_id = current_user.id     │  │
│  │  - Verifies Google OIDC tokens with Google Auth Servers               │  │
│  │  - Validates & rotates hashed Refresh Tokens from Database            │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Business Service Layer (expense, budget, category, dashboard, auth)   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │ asyncpg (Pooled Connection)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PostgreSQL Database (Supabase)                        │
│  - users (id, email, hashed_password, google_id, is_verified, ...)         │
│  - refresh_tokens (token_hash, user_id, expires_at, revoked)                │
│  - password_reset_tokens (token_hash, user_id, expires_at, used)            │
│  - expenses (user_id FK, title, amount, category_id FK, date, ...)          │
│  - budgets (user_id FK, scope, category_id FK, period_month, limit, ...)    │
│  - categories (user_id FK NULL for defaults, name, is_default, ...)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema (PostgreSQL)

### 3.1 Table: `users`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| email | VARCHAR(255) | NOT NULL, UNIQUE (case-insensitive via functional index `lower(email)`) |
| hashed_password | VARCHAR(255) | NULL (null if user signed up solely via Google OAuth) |
| full_name | VARCHAR(100) | NULL |
| google_id | VARCHAR(255) | NULL, UNIQUE (linked Google account identifier) |
| avatar_url | VARCHAR(512) | NULL |
| is_verified | BOOLEAN | NOT NULL, default `false` (Google accounts auto-verified `true`) |
| is_active | BOOLEAN | NOT NULL, default `true` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Indexes: `idx_users_email_lower` (unique, `lower(email)`), `idx_users_google_id` (unique where `google_id IS NOT NULL`).

### 3.2 Table: `refresh_tokens`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| token_hash | VARCHAR(255) | NOT NULL, UNIQUE (SHA-256 or bcrypt hash of raw refresh token) |
| user_id | UUID | NOT NULL, FK → `users.id`, `ON DELETE CASCADE` |
| user_agent | VARCHAR(255) | NULL (device / browser metadata) |
| ip_address | VARCHAR(45) | NULL (client IP for audit) |
| expires_at | TIMESTAMPTZ | NOT NULL |
| revoked | BOOLEAN | NOT NULL, default `false` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Indexes: `idx_refresh_tokens_hash` (unique), `idx_refresh_tokens_user_id` (`user_id`).

### 3.3 Table: `password_reset_tokens`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| token_hash | VARCHAR(255) | NOT NULL, UNIQUE (SHA-256 hash of random reset secret) |
| user_id | UUID | NOT NULL, FK → `users.id`, `ON DELETE CASCADE` |
| expires_at | TIMESTAMPTZ | NOT NULL (short-lived: e.g. 1 hour) |
| used | BOOLEAN | NOT NULL, default `false` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |

Indexes: `idx_password_reset_tokens_hash` (unique), `idx_password_reset_user_id` (`user_id`).

### 3.4 Table: `categories`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| user_id | UUID | NULL, FK → `users.id`, `ON DELETE CASCADE` (NULL for global seeded defaults; populated for user custom categories) |
| name | VARCHAR(50) | NOT NULL |
| is_default | BOOLEAN | NOT NULL, default `false` |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Indexes:
- Unique category name per user: `idx_categories_user_name_unique` (unique on `(COALESCE(user_id, '00000000-0000-0000-0000-000000000000'), lower(name))`).

### 3.5 Table: `expenses`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| user_id | UUID | NOT NULL, FK → `users.id`, `ON DELETE CASCADE` |
| title | VARCHAR(50) | NOT NULL |
| category_id | UUID | NOT NULL, FK → `categories.id`, `ON DELETE RESTRICT` |
| amount | NUMERIC(12,2) | NOT NULL, CHECK (`amount > 0`) |
| expense_date | DATE | NOT NULL, CHECK (`expense_date <= CURRENT_DATE`) |
| notes | TEXT | NULL |
| payment_mode | VARCHAR(20) | NULL, CHECK IN (`'cash','card','upi','other'`) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Indexes: `idx_expenses_user_id` (`user_id`), `idx_expenses_user_date` (`user_id`, `expense_date`), `idx_expenses_user_category` (`user_id`, `category_id`), `idx_expenses_user_amount` (`user_id`, `amount`).

### 3.6 Table: `budgets`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| user_id | UUID | NOT NULL, FK → `users.id`, `ON DELETE CASCADE` |
| scope | VARCHAR(10) | NOT NULL, CHECK IN (`'overall','category'`) |
| category_id | UUID | NULL, FK → `categories.id`, `ON DELETE CASCADE` |
| period_month | DATE | NOT NULL (first day of month, e.g. `2026-08-01`) |
| limit_amount | NUMERIC(12,2) | NOT NULL, CHECK (`limit_amount > 0`) |
| created_at | TIMESTAMPTZ | NOT NULL, default `now()` |
| updated_at | TIMESTAMPTZ | NOT NULL, default `now()`, auto-updated |

Unique constraints:
- Overall budget per user per month: `idx_budgets_unique_user_overall` (unique on `(user_id, scope, period_month)` where `category_id IS NULL`).
- Category budget per user per category per month: `idx_budgets_unique_user_category` (unique on `(user_id, scope, category_id, period_month)` where `category_id IS NOT NULL`).

---

## 4. Authentication, Authorization & Security Architecture

### 4.1 JWT Token Architecture

1. **Access Token:**
   - Lifetime: **15 minutes**.
   - Payload: `sub` (`user_id` as UUID string), `email`, `exp`, `iat`, `type: "access"`.
   - Signed using `HMAC-SHA256` (`HS256`) with `JWT_SECRET` key stored in backend `.env` only.
   - Sent via HTTP Header: `Authorization: Bearer <access_token>`.
   - Stored on Frontend in **React Memory / AuthContext** (never in `localStorage` or `sessionStorage` to mitigate XSS exposure).

2. **Refresh Token:**
   - Lifetime: **14 days** (configurable up to 30 days).
   - Format: High-entropy cryptographically secure random string (e.g. 64 characters via `secrets.token_urlsafe(64)`).
   - Storage in Database: **SHA-256 hash** only (`token_hash`), never raw string.
   - Transmission to Client: Set via **`HttpOnly`**, **`Secure`**, **`SameSite=Lax`** (or `Strict` for same-origin) cookie on path `/api/auth`.
   - Inaccessible to client-side JavaScript.

3. **Refresh Token Rotation (RTR):**
   - Whenever `/api/auth/refresh` is requested with a valid cookie:
     1. The server validates the refresh token hash against the database.
     2. If valid and not revoked/expired, the existing refresh token is marked `revoked = true` (or deleted).
     3. A new Access Token + new Refresh Token pair is generated.
     4. The new refresh token hash is saved to the DB, and the new cookie is returned to the client.
   - **Reuse Detection:** If an already-revoked refresh token is presented, the server revokes all active refresh tokens for that user immediately, as it indicates a token compromise.

4. **Revocation & Logout:**
   - `POST /api/auth/logout`: Revokes the specific refresh token associated with the cookie and clears the cookie (`Max-Age=0`).
   - `POST /api/auth/logout-all`: Sets `revoked = true` for all active refresh tokens for the authenticated user, terminating all sessions across all devices.

### 4.2 Google Sign-In (OAuth 2.0 / OpenID Connect)

1. Frontend initiates Google Sign-In via Google Identity Services and receives an ID token (`credential`).
2. Frontend sends `POST /api/auth/google` with `{ "id_token": string }`.
3. Backend validates the ID token signature, `aud` (matching `GOOGLE_CLIENT_ID`), `iss` (`https://accounts.google.com`), and expiration against Google's public certs.
4. Backend extracts `sub` (Google user ID), `email`, `name`, and `picture`.
5. **Account Linking Logic:**
   - If a user exists with matching `google_id` → Log them in.
   - If a user exists with matching `email` (from password signup) → Link `google_id = sub`, set `is_verified = true`, and log them in safely.
   - If no user exists → Create a new user record (`email`, `google_id`, `full_name`, `is_verified = true`, `hashed_password = NULL`), clone default starter categories for them, and issue tokens.
6. Return standard application Access Token + HttpOnly Refresh Token cookie.

### 4.3 Password & Security Controls

- **Hashing:** Argon2id or BCrypt (`rounds=12`) with unique cryptographically secure salts. Plaintext passwords are never logged or stored.
- **Password Strength:** Minimum 8 characters, containing at least one uppercase letter, one lowercase letter, and one number.
- **Forgot / Reset Password Flow:**
  1. `POST /api/auth/forgot-password`: Generates a single-use crypto-random token, stores its SHA-256 hash in `password_reset_tokens` (expires in 1 hour), and dispatches a reset link to the registered email. Always returns generic success to prevent email enumeration.
  2. `POST /api/auth/reset-password`: Validates token hash, ensures `used = false` and `expires_at > now()`, hashes the new password, updates user record, marks token `used = true`, and revokes all existing refresh tokens.
- **Rate Limiting:**
  - `POST /api/auth/login`: 5 requests per minute per IP / email.
  - `POST /api/auth/register`: 3 requests per minute per IP.
  - `POST /api/auth/forgot-password`: 3 requests per 15 minutes per IP / email.
- **CORS & CSRF Security:**
  - CORS strictly configured to allow trusted origins (`http://localhost:3000` locally, Vercel domain in production).
  - `allow_credentials=True` enabled with explicit origin matching (never wildcard `*` with credentials).
  - SameSite cookie policies prevent cross-site request forgery on token refresh.

---

## 5. User Data Isolation Architecture (Mandatory Rule)

> [!IMPORTANT]
> **Zero Trust on Frontend Identifiers:** The backend **never** relies on any `user_id` passed in request payloads, headers, or query parameters. The authenticated user ID is derived strictly from the cryptographically verified JWT token via FastAPI's `get_current_user` dependency.

### 5.1 Enforced Isolation Across Services

Every service query must explicitly scope operations to `current_user.id`:

```python
# Expenses
select(Expense).where(Expense.user_id == current_user.id, ...)
select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id)

# Budgets
select(Budget).where(Budget.user_id == current_user.id, ...)

# Dashboard Analytics
select(func.sum(Expense.amount)).where(Expense.user_id == current_user.id, ...)

# Categories
select(Category).where(or_(Category.user_id == current_user.id, Category.is_default == True))
```

- If User A attempts to `GET`, `PUT`, or `DELETE /api/expenses/{id}` where `{id}` belongs to User B, the backend returns **`404 Not Found`** (or `403 Forbidden`), preventing User A from discovering or modifying User B's records.

---

## 6. API Contract Specification

All endpoints require `Authorization: Bearer <token>` except public authentication routes and `/api/health`.

### 6.1 Authentication Endpoints (`/api/auth`)

| Method | Endpoint | Auth Required | Description | Request Body / Params | Response Codes |
|---|---|---|---|---|---|
| POST | `/api/auth/register` | No | Register new email/password account | `{ "email": "user@example.com", "password": "...", "full_name": "..." }` | `201 Created`, `400`, `409 Conflict` |
| POST | `/api/auth/login` | No | Authenticate user & issue tokens | `{ "email": "user@example.com", "password": "..." }` | `200 OK` (returns `{ access_token, user }`, sets HttpOnly cookie), `401 Unauthorized` |
| POST | `/api/auth/google` | No | Authenticate via Google ID token | `{ "id_token": "..." }` | `200 OK` (returns `{ access_token, user }`, sets HttpOnly cookie), `400 Bad Request` |
| POST | `/api/auth/refresh` | No (Cookie) | Rotate refresh token & issue new access token | Uses `refresh_token` HttpOnly cookie | `200 OK` (returns `{ access_token }`), `401 Unauthorized` |
| POST | `/api/auth/logout` | Yes | Revoke current session & clear cookie | None (uses cookie + Bearer) | `200 OK` (clears cookie) |
| POST | `/api/auth/logout-all` | Yes | Revoke all active sessions on all devices | None | `200 OK` |
| POST | `/api/auth/forgot-password` | No | Request password reset email | `{ "email": "user@example.com" }` | `200 OK` |
| POST | `/api/auth/reset-password` | No | Reset password using reset token | `{ "token": "...", "new_password": "..." }` | `200 OK`, `400 Bad Request` |
| POST | `/api/auth/change-password` | Yes | Change password while logged in | `{ "current_password": "...", "new_password": "..." }` | `200 OK`, `400`, `401` |
| GET | `/api/auth/me` | Yes | Retrieve profile of authenticated user | None | `200 OK` (returns `UserResponse`) |

### 6.2 Application Endpoints (User-Scoped)

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| GET | `/api/health` | No | System & database health probe |
| GET | `/api/expenses` | Yes (Bearer) | Filtered, sorted, paginated expenses belonging **only** to current user |
| POST | `/api/expenses` | Yes (Bearer) | Create new expense automatically bound to `current_user.id` |
| GET | `/api/expenses/{id}` | Yes (Bearer) | Retrieve single expense if owned by `current_user.id` |
| PUT | `/api/expenses/{id}` | Yes (Bearer) | Update expense if owned by `current_user.id` |
| DELETE | `/api/expenses/{id}` | Yes (Bearer) | Delete expense if owned by `current_user.id` |
| GET | `/api/categories` | Yes (Bearer) | List global default categories + user's custom categories |
| POST | `/api/categories` | Yes (Bearer) | Create new category for `current_user.id` |
| PUT | `/api/categories/{id}` | Yes (Bearer) | Rename custom category owned by `current_user.id` |
| DELETE | `/api/categories/{id}` | Yes (Bearer) | Delete custom category owned by `current_user.id` |
| GET | `/api/budgets` | Yes (Bearer) | List monthly budgets configured by `current_user.id` |
| POST | `/api/budgets` | Yes (Bearer) | Create budget goal for `current_user.id` |
| PUT | `/api/budgets/{id}` | Yes (Bearer) | Update budget goal for `current_user.id` |
| DELETE | `/api/budgets/{id}` | Yes (Bearer) | Remove budget goal for `current_user.id` |
| GET | `/api/budgets/status` | Yes (Bearer) | Live computed spending vs limits for `current_user.id` |
| GET | `/api/dashboard/*` | Yes (Bearer) | Summary, charts, trends, and MoM analytics for `current_user.id` |

### 6.3 AI Recommendation & Financial Health Endpoints (`/api/ai`)

| Method | Endpoint | Auth Required | Description | Request Body / Params | Response Codes |
|---|---|---|---|---|---|
| GET | `/api/ai/health-score` | Yes (Bearer) | Retrieve real-time Financial Health Score (0–100) with metric breakdowns | `?month=X&year=Y` (defaults to current) | `200 OK` (returns `HealthScoreResponse`) |
| GET | `/api/ai/monthly-summary` | Yes (Bearer) | Retrieve cached or generated monthly AI executive digest and actionable tips | `?month=X&year=Y` (defaults to current) | `200 OK` (returns `MonthlySummaryResponse`) |
| POST | `/api/ai/monthly-summary/generate` | Yes (Bearer) | Force regenerate AI analysis and advice via Google Gemini | `?month=X&year=Y` | `200 OK`, `429 Too Many Requests` |

---

## 7. AI Recommendation & Financial Health Scoring Architecture

### 7.1 Algorithmic Financial Health Scoring Model (0–100)

The Financial Health Score is computed deterministically via a weighted multi-factor algorithm:

$$\text{Health Score} = (0.40 \times \text{Budget Adherence}) + (0.30 \times \text{Savings/Spend Velocity}) + (0.20 \times \text{Category Diversity}) + (0.10 \times \text{Expense Regularity})$$

| Component | Weight | Calculation Method | Scoring Scale |
|---|---|---|---|
| **Budget Adherence** | 40% | Measures whether expenses stay below set category/overall limits. Deducts points proportionally for overspent budgets. | 0–100 (100 = All budgets <= 80% utilized) |
| **Spending Velocity** | 30% | Compares daily spending rate against month progress. Detects if user is on track to exhaust budget before month-end. | 0–100 (100 = Controlled uniform daily pace) |
| **Category Diversification** | 20% | Evaluates whether spending is dangerously concentrated in a single discretionary bucket (e.g. >60% in Shopping/Entertainment). | 0–100 (100 = Balanced allocation across life categories) |
| **Expense Regularity** | 10% | Assesses consistent logging habits and absence of chaotic impulse spikes (>3x average transaction). | 0–100 (100 = Smooth transaction distribution) |

#### Score Tier Classifications:
- **85 – 100:** 🟢 **Excellent** (Strong savings habits, optimal budget adherence)
- **70 – 84:** 🔵 **Good** (Healthy management, minor category overages)
- **50 – 69:** 🟡 **Fair** (Budget pressure, high discretionary concentration)
- **0 – 49:** 🔴 **Needs Attention** (Exceeded multiple budgets, high spending velocity)

---

### 7.2 Google Gemini LLM Integration & Structured Schema

FinTrack uses Google's `gemini-1.5-flash` model via the Google GenAI SDK to generate personalized monthly executive summaries and actionable advice:

1. **Strict Data Anonymization:** Only aggregated numerical metrics (totals, category percentages, budget overage amounts, and top merchant descriptions) are passed into the prompt. **Zero PII (email, password, user names, or tokens) is ever transmitted to the LLM.**
2. **Strict User Scoping:** The data payload fed into the prompt is generated strictly from `current_user.id` records.
3. **Structured JSON Output:** Gemini is invoked with schema enforcement (`response_mime_type="application/json"`), ensuring guaranteed parsing into Pydantic models without brittle regex.

#### Expected LLM Output Schema:
```json
{
  "score": 82,
  "status": "Good",
  "executive_summary": "In September, your total expenditure was ₹24,500 across 32 transactions...",
  "top_category": {
    "name": "Food & Dining",
    "amount": 9200,
    "percentage": 37.5
  },
  "key_win": "Your transportation spending dropped by 22% compared to last month.",
  "biggest_expense": {
    "description": "Electronics Store",
    "amount": 5400,
    "date": "2026-09-12"
  },
  "actionable_recommendations": [
    "Cap weekend dining out to reduce Food expenses by ~₹2,500 next month.",
    "Set a ₹4,000 budget limit on Entertainment to keep your velocity on track.",
    "Review your 2 recurring streaming subscriptions before renewal on the 15th."
  ]
}
```

---

### 7.3 Database Caching & Performance Optimization

To prevent unnecessary API latency and avoid redundant LLM cost:
- A new table `financial_health_summaries` is introduced:
  - `id`: UUID Primary Key
  - `user_id`: UUID Foreign Key to `users.id` (Indexed, Cascade Delete)
  - `month`: Integer (1–12)
  - `year`: Integer
  - `score`: Integer (0–100)
  - `status`: String (e.g. "Excellent", "Good", "Fair", "Needs Attention")
  - `summary_json`: JSONB (storing executive summary, top category, key win, recommendations)
  - `created_at` & `updated_at`: Timestamps
- **Cache Invalidation Policy:** Results are cached per `(user_id, month, year)`. When a user logs or deletes expenses in the current month, the score recalculates dynamically in-memory; the full LLM executive summary can be re-analyzed on-demand with a 15-minute rate limit.

---

## 8. Folder Structure

```
fintrack/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, rate limiting, exception handlers
│   │   ├── config.py                # Settings (JWT_SECRET, GOOGLE_CLIENT_ID, SMTP, etc.)
│   │   ├── core/
│   │   │   ├── security.py          # Password hashing, JWT encode/decode, crypto helpers
│   │   │   ├── exceptions.py        # UnauthorizedException, ForbiddenException, etc.
│   │   │   └── limiter.py           # Rate limiting configuration (slowapi)
│   │   ├── db/
│   │   │   ├── session.py           # SQLAlchemy async engine
│   │   │   ├── base.py              # Declarative base importing all models
│   │   │   └── seed.py              # Idempotent starter category seeding
│   │   ├── models/
│   │   │   ├── user.py              # User model
│   │   │   ├── refresh_token.py     # RefreshToken model
│   │   │   ├── password_reset.py    # PasswordResetToken model
│   │   │   ├── category.py          # Category model (with user_id)
│   │   │   ├── expense.py           # Expense model (with user_id)
│   │   │   └── budget.py            # Budget model (with user_id)
│   │   ├── schemas/
│   │   │   ├── auth.py              # Auth request/response schemas (Register, Login, Token, etc.)
│   │   │   ├── user.py              # User profile schemas
│   │   │   ├── category.py
│   │   │   ├── expense.py
│   │   │   └── budget.py
│   │   ├── services/
│   │   │   ├── auth_service.py      # Registration, login, token rotation, Google verification
│   │   │   ├── email_service.py     # Password reset & verification email delivery
│   │   │   ├── expense_service.py   # User-scoped expense business logic
│   │   │   ├── category_service.py  # User-scoped category logic
│   │   │   ├── budget_service.py    # User-scoped budget logic
│   │   │   └── dashboard_service.py # User-scoped analytics logic
│   │   └── api/
│   │       ├── deps.py              # get_current_user, get_db, pagination
│   │       └── v1/
│   │           ├── router.py        # Centralized router
│   │           ├── auth.py          # /api/auth routes
│   │           ├── expenses.py
│   │           ├── categories.py
│   │           ├── budgets.py
│   │           ├── dashboard.py
│   │           └── health.py
│   ├── alembic/
│   │   └── versions/                # Migrations for users, tokens, and user_id foreign keys
│   └── tests/
│       ├── test_auth.py             # Unit/integration tests for register, login, refresh, logout
│       ├── test_data_isolation.py   # Cross-user data isolation penetration tests
│       ├── test_expenses.py
│       ├── test_categories.py
│       ├── test_budgets.py
│       └── test_dashboard.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/              # Unauthenticated routes (clean layout)
│   │   │   │   ├── login/page.tsx
│   │   │   │   ├── register/page.tsx
│   │   │   │   ├── forgot-password/page.tsx
│   │   │   │   └── reset-password/page.tsx
│   │   │   ├── (dashboard)/         # Authenticated app routes (wrapped in AppShell & route guard)
│   │   │   │   ├── dashboard/page.tsx
│   │   │   │   ├── expenses/page.tsx
│   │   │   │   └── categories/page.tsx
│   │   │   ├── layout.tsx           # Root layout with Providers
│   │   │   └── providers.tsx        # QueryClientProvider + AuthProvider + GoogleOAuthProvider
│   │   ├── context/
│   │   │   └── AuthContext.tsx      # Auth state, login(), logout(), token refresh cycle
│   │   ├── hooks/
│   │   │   └── useAuth.ts           # useAuth hook
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   ├── RegisterForm.tsx
│   │   │   │   ├── GoogleSignInButton.tsx
│   │   │   │   └── ResetPasswordForm.tsx
│   │   │   └── layout/
│   │   │       ├── AppShell.tsx
│   │   │       └── UserProfileDropdown.tsx
│   │   └── lib/
│   │       ├── api-client.ts        # Axios with withCredentials & 401 token refresh interceptor
│   │       └── validators/
│   │           └── auth.ts          # Zod schemas for login, register, password reset
```

---

## 8. Environment Configuration

### 8.1 `backend/.env.example`

```env
# App
APP_ENV=development
APP_NAME=FinTrack API
API_PORT=8000
LOG_LEVEL=INFO

# Database (PostgreSQL / Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fintrack_db

# CORS (Frontend origin)
CORS_ORIGINS=http://localhost:3000

# Authentication & JWT Secrets
JWT_SECRET=super_secret_cryptographic_random_key_min_32_chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=14

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email / SMTP (Password Reset)
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=your_smtp_api_key
EMAILS_FROM_EMAIL=noreply@fintrack.app
EMAILS_FROM_NAME="FinTrack Security"
FRONTEND_URL=http://localhost:3000
```

### 8.2 `frontend/.env.example`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_NAME=FinTrack
NEXT_PUBLIC_DEFAULT_CURRENCY=INR
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

---

## 9. Testing & Quality Assurance Plan

The test suite must verify the following scenarios before release:

1. **Authentication Tests (`test_auth.py`):**
   - User registration with valid email & strong password.
   - Rejection of duplicate email registration (`409 Conflict`).
   - Successful login returning short-lived access token and HttpOnly refresh token cookie.
   - Login failure on invalid credentials with generic error message (`401 Unauthorized`).
   - Token refresh issuing new access token + new rotated refresh token.
   - Revocation of refresh tokens upon logout and logout-all.
   - Reuse detection: presenting an already-revoked refresh token revokes all user sessions.
   - Forgot password and reset password flow with expiration check.
   - Rate limiting enforcement on `/auth/login` and `/auth/register`.

2. **Data Isolation Tests (`test_data_isolation.py`):**
   - User A logs 3 expenses; User B logs 2 expenses.
   - User A calling `GET /api/expenses` receives only User A's 3 expenses.
   - User A calling `GET /api/expenses/{User_B_expense_id}` receives `404 Not Found`.
   - User A calling `PUT` or `DELETE /api/expenses/{User_B_expense_id}` receives `404 Not Found` and User B's expense remains unchanged.
   - User A calling `GET /api/dashboard/summary` receives totals computed solely from User A's expenses.
   - User A calling `GET /api/budgets/status` sees only User A's budgets and spending against them.

3. **Frontend Integration Verification:**
   - Unauthenticated access to protected routes redirects to `/login`.
   - Google Sign-In button handles popup, receives token, calls backend, and logs user into dashboard.
   - Seamless token renewal in background before access token expiration.
   - 401 response handling: transparently refreshes access token or redirects to login if refresh token expired.
