# FinTrack — Session Progress & Memory Report

## Session Date: 2026-09-02 & 2026-09-03
**Current Branch:** `main`  
**Latest Commit:** `d7a6190` (`fix(db): ensure all tables are auto-created in Supabase on startup and improve Resend error feedback`)
**Live Production Deployments:**
- **Frontend (Vercel):** `https://fin-track-two-lovat.vercel.app`
- **Backend (Render):** `https://fin-track-mngi.onrender.com`
- **Database (Supabase):** PostgreSQL with Session Pooler on AWS

---

## 1. Accomplishments in This Session

### A. Non-Technical & Technical Requirements
- **PRD Updated:** [FinTrack_PRD.md](file:///d:/FinTrack/docs/FinTrack_PRD.md) with complete non-technical user stories covering user accounts, email verification OTP, authentication workflows, password resets, and user data isolation.
- **SRS Updated:** [FinTrack_SRS.md](file:///d:/FinTrack/docs/FinTrack_SRS.md) detailing JWT specifications (HS256, 15m access / 14d refresh), Refresh Token Rotation (RTR), reuse detection, `HttpOnly` cookie policies, Google OIDC backend verification, and strict user isolation queries.

### B. Email Verification Code (OTP) Registration System
- **Database Model & Migration:** Added [email_verification.py](file:///d:/FinTrack/backend/app/models/email_verification.py) (`EmailVerificationCode`) storing SHA-256 OTP hashes with 10-minute expiry and 5-attempt brute-force protection. Successfully applied migration `09dbad68cd7e_add_email_verification_codes.py`.
- **Automatic Supabase Table Creation:** Updated FastAPI lifespan in [main.py](file:///d:/FinTrack/backend/app/main.py) to run `Base.metadata.create_all` automatically on boot so tables are guaranteed to exist in Supabase.
- **Hybrid Email Dispatcher ([email_service.py](file:///d:/FinTrack/backend/app/services/email_service.py)):**
  - **Local Development:** Standard/Google SMTP (`smtp.gmail.com:587`) via `_send_smtp_sync`.
  - **Production:** Resend REST API via `httpx.AsyncClient` (`https://api.resend.com/emails`) when `RESEND_API_KEY` is provided. Uses `onboarding@resend.dev` as the default test sender or custom verified domains.
  - **Fallback:** Development console logging with `[DEV EMAIL]` tags.
  - **Error Feedback:** Explicit error propagation so invalid emails or provider rejections show up transparently in the UI.
- **Backend Auth Endpoints & Service:**
  - `POST /api/auth/send-verification-code`: Dispatches 6-digit OTP code, invalidates previous codes, enforces rate limiting.
  - `POST /api/auth/register`: Requires `code` matching SHA-256 hash in DB before creating active user account with `is_verified=True`.
- **Frontend 2-Step Registration UI ([register/page.tsx](file:///d:/FinTrack/frontend/src/app/register/page.tsx)):**
  - Progressive step flow: Step 1 (Credentials) -> Step 2 (6-digit OTP input with paste support, auto-focus, and 60-second resend countdown).
  - Celebration banner with `"User successfully registered! Redirecting to dashboard..."` and delayed router push.

### C. Google OAuth & Password Coexistence (Seamless Account Linking)
- **Unified Dual Sign-In ([auth_service.py](file:///d:/FinTrack/backend/app/services/auth_service.py)):**
  - Users registered with Email + Password can also sign in via Google with that same email. Google ID is linked and the existing hashed password is never overwritten.
  - Users created via Google attempting email/password login receive a clear prompt to use Google Sign-In or "Forgot Password".
  - Resilient token verification with clock skew tolerance and strict client ID validation.

### D. Production Deployment Verification
- Render web service (`https://fin-track-mngi.onrender.com`) verified live and passing health checks.
- Live `POST /api/auth/send-verification-code` verified on Render, successfully dispatching real OTP emails via Resend.
- Vercel frontend (`https://fin-track-two-lovat.vercel.app`) configured with `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_GOOGLE_CLIENT_ID`.

### E. Verification & Testing
- **Backend Tests:** **25 / 25 pytest tests passed (100%)** including full OTP send, validation, expiration, and invalid attempt test cases in [test_auth.py](file:///d:/FinTrack/backend/tests/test_auth.py).
- **Frontend Tests & Build:** `npm run build` compiled cleanly with 0 TypeScript/ESLint errors across all 14 routes.

---

## 2. Current Project State
- **Backend:** Production-ready FastAPI service with secure JWT auth, Google OIDC token verification, 6-digit email OTP verification (Google SMTP locally / Resend API in prod), refresh token rotation, rate limiting, and strict user data isolation.
- **Frontend:** Next.js 14 App Router application with progressive 2-step OTP registration, auth context, silent token refresh, sleek auth views, protected dashboard/expense/category routes, and profile session controls.

---

## 3. Server Startup Commands
- **Backend (Local):** `cd d:\FinTrack\backend; .\venv\Scripts\activate; uvicorn app.main:app --reload --port 8000`
- **Frontend (Local):** `cd d:\FinTrack\frontend; npm run dev`
- **Database Cleanup Tool:** `cd d:\FinTrack\backend; .\venv\Scripts\python.exe delete_user.py <email>`
