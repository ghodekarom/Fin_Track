# FinTrack — Session Progress & Memory Report

## Session Date: 2026-08-31
**Current Branch:** `main`  
**Latest Commit:** `58a467b` (`feat(auth): implement production-ready JWT auth, Google OIDC, and strict user data isolation`)

---

## 1. Accomplishments in This Session

### A. Non-Technical & Technical Requirements Update
- **PRD Updated:** Updated [FinTrack_PRD.md](file:///d:/FinTrack/docs/FinTrack_PRD.md) with complete non-technical user stories covering user accounts, authentication workflows, password resets, and user data isolation.
- **SRS Updated:** Updated [FinTrack_SRS.md](file:///d:/FinTrack/docs/FinTrack_SRS.md) to technical v4.0 detailing JWT specifications (HS256, 15m access / 14d refresh), Refresh Token Rotation (RTR), reuse detection, `HttpOnly` cookie policies, Google OIDC backend verification, and strict user isolation queries.

### B. Backend Authentication & Security Architecture
- **Dependencies Installed:** `python-jose[cryptography]`, `bcrypt`, `google-auth`, `requests`, `email-validator`, `slowapi`, `httpx`.
- **Configuration:** Updated [config.py](file:///d:/FinTrack/backend/app/config.py) and [backend/.env.example](file:///d:/FinTrack/backend/.env.example) to support all JWT, Google OAuth, SMTP email, and rate-limiting environment variables.
- **Security Core ([security.py](file:///d:/FinTrack/backend/app/core/security.py)):** Direct bcrypt password hashing (rounds=12), SHA-256 token hashing, high-entropy random token generation, and HS256 JWT access token signing/decoding.
- **Rate Limiting ([limiter.py](file:///d:/FinTrack/backend/app/core/limiter.py)):** Integrated `slowapi` rate limiter on auth routes (`login`: 5/min, `auth`: 10/min, `reset`: 3/min).
- **Database Models & Alembic Migration:**
  - Added [user.py](file:///d:/FinTrack/backend/app/models/user.py) (`User`), [refresh_token.py](file:///d:/FinTrack/backend/app/models/refresh_token.py) (`RefreshToken`), and [password_reset.py](file:///d:/FinTrack/backend/app/models/password_reset.py) (`PasswordResetToken`).
  - Updated `Expense`, `Budget`, `Category` models with `user_id` foreign keys and indices.
  - Generated and successfully executed migration `8b1850972073_add_auth_and_user_data_isolation.py` on remote PostgreSQL/Supabase database.
- **Services & Routes:**
  - [auth_service.py](file:///d:/FinTrack/backend/app/services/auth_service.py): Registration, login, Google OIDC ID token verification, refresh token rotation (with reuse detection that invalidates all sessions upon token replay), session revocation, password reset, and change password.
  - [email_service.py](file:///d:/FinTrack/backend/app/services/email_service.py): Asynchronous password reset dispatcher with development console fallback.
  - [auth.py](file:///d:/FinTrack/backend/app/api/v1/auth.py): Mounted `/api/auth/*` router (`/register`, `/login`, `/google`, `/refresh`, `/logout`, `/logout-all`, `/forgot-password`, `/reset-password`, `/change-password`, `/me`).

### C. Strict User Data Isolation
- `get_current_user` in [deps.py](file:///d:/FinTrack/backend/app/api/deps.py) decodes the Bearer JWT and injects `current_user`. The API never accepts or trusts client-supplied `user_id`.
- Updated [expense_service.py](file:///d:/FinTrack/backend/app/services/expense_service.py), [budget_service.py](file:///d:/FinTrack/backend/app/services/budget_service.py), [category_service.py](file:///d:/FinTrack/backend/app/services/category_service.py), and [dashboard_service.py](file:///d:/FinTrack/backend/app/services/dashboard_service.py) so that **every query and database operation is strictly scoped to `user_id == current_user.id`**.
- Default starter categories (`user_id IS NULL`) are globally accessible read-only; user custom categories are private and editable/deletable only by their creator.

### D. Frontend Authentication & UI Pages
- **Installed `@react-oauth/google`** for frontend Google Identity Services.
- **API Client ([api-client.ts](file:///d:/FinTrack/frontend/src/lib/api-client.ts)):** Configured `withCredentials: true`, in-memory token state, Bearer request interceptor, and 401 response interceptor with silent token refresh queue.
- **Auth Context & Hook ([AuthContext.tsx](file:///d:/FinTrack/frontend/src/context/AuthContext.tsx), [useAuth.ts](file:///d:/FinTrack/frontend/src/hooks/useAuth.ts)):** Provides user state, silent initialization on app load, login, registration, Google auth, logout, and multi-device logout.
- **New Auth UI Pages:**
  - [Login Page](file:///d:/FinTrack/frontend/src/app/login/page.tsx): Glassmorphism dark UI, email/password validation, Google Sign-In button.
  - [Register Page](file:///d:/FinTrack/frontend/src/app/register/page.tsx): Account creation with password confirmation and Google Sign-In.
  - [Forgot Password Page](file:///d:/FinTrack/frontend/src/app/forgot-password/page.tsx): Email dispatch form with clear status feedback.
  - [Reset Password Page](file:///d:/FinTrack/frontend/src/app/reset-password/page.tsx): Token-validated password update form.
- **AppShell ([AppShell.tsx](file:///d:/FinTrack/frontend/src/components/layout/AppShell.tsx)):** Route protection (redirects unauthenticated users to `/login`), clean auth layout, profile avatar, user email badge, and dropdown menu with "Log Out" and "Log Out All Devices".

### F. Email Verification Code (OTP) Registration System
- **Database Model & Migration:** Added [email_verification.py](file:///d:/FinTrack/backend/app/models/email_verification.py) (`EmailVerificationCode`) storing SHA-256 OTP hashes with 10-minute expiry and 5-attempt brute-force protection. Successfully applied migration `09dbad68cd7e_add_email_verification_codes.py`.
- **Hybrid Email Dispatcher ([email_service.py](file:///d:/FinTrack/backend/app/services/email_service.py)):**
  - **Local Development:** Standard/Google SMTP (`smtp.gmail.com:587`) via `_send_smtp_sync`.
  - **Production:** Resend REST API via `httpx.AsyncClient` (`https://api.resend.com/emails`) when `RESEND_API_KEY` is provided.
  - **Fallback:** Development console logging with `[DEV EMAIL]` tags.
- **Backend Auth Endpoints & Service:**
  - `POST /api/auth/send-verification-code`: Dispatches 6-digit OTP code, invalidates previous codes, enforces 5/10min rate limiting.
  - `POST /api/auth/register`: Requires `code` matching SHA-256 hash in DB before creating active user account with `is_verified=True`.
- **Frontend 2-Step Registration UI ([register/page.tsx](file:///d:/FinTrack/frontend/src/app/register/page.tsx)):**
  - Progressive step flow: Step 1 (Credentials) -> Step 2 (6-digit OTP input with paste support, auto-focus, and 60-second resend countdown).
  - Context & types updated in [AuthContext.tsx](file:///d:/FinTrack/frontend/src/context/AuthContext.tsx) and [auth.ts](file:///d:/FinTrack/frontend/src/types/auth.ts).

### G. Verification & Testing
- **Backend Tests:** **25 / 25 pytest tests passed (100%)** including full OTP send, validation, expiration, and invalid attempt test cases in [test_auth.py](file:///d:/FinTrack/backend/tests/test_auth.py).
- **Frontend Tests & Build:** `npm run build` compiled cleanly with 0 TypeScript/ESLint errors across all 14 routes.

---

## 2. Current Project State
- **Backend:** Production-ready FastAPI service with secure JWT auth, Google OIDC token verification, 6-digit email OTP verification (Google SMTP locally / Resend API in prod), refresh token rotation, rate limiting, and strict user data isolation.
- **Frontend:** Next.js 14 App Router application with progressive 2-step OTP registration, auth context, silent token refresh, sleek auth views, protected dashboard/expense/category routes, and profile session controls.

---

## 3. Server Startup Commands
- **Backend:** `cd d:\FinTrack\backend; .\venv\Scripts\activate; uvicorn app.main:app --reload --port 8000`
- **Frontend:** `cd d:\FinTrack\frontend; npm run dev`
