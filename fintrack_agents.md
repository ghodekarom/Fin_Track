# FinTrack — AGENTS.md

## 1. Core Project Rules

1. **Conversation Rule:** Start every project-related conversation/response with **“Om Bhai”**.
2. **Follow the PRD and SRS strictly.** They are the primary source of truth for V1 scope, functionality, architecture, schemas, API contracts, UI/UX, and non-functional requirements.
3. **Do not invent or silently change requirements.** If a requirement is unclear or conflicts with the PRD/SRS, stop and ask before implementing.
4. **Stay within V1 scope.** Do not pull Phase 2+ features into V1 unless explicitly approved.
5. **Do not change the approved project architecture or tech stack without approval.**

## 2. Architecture Rules

6. Follow the approved architecture exactly:
   **Next.js → FastAPI → PostgreSQL**.
7. **Frontend must never access PostgreSQL directly.** All application data must flow through the FastAPI REST API.
8. Keep the backend stateless for V1.
9. Respect the defined backend/frontend folder structure and separation of concerns.
10. Keep business logic in backend service layers; do not put core business logic directly inside route handlers or UI components.

## 3. Environment & Security Rules

11. **No hardcoded secrets, credentials, URLs, passwords, tokens, API keys, or environment-specific configuration.**
12. Use `.env` / `.env.local` locally and platform environment variables in production.
13. Never commit real `.env` or secret values to Git.
14. Keep `.env.example` files updated whenever a new environment variable is required.
15. Treat `NEXT_PUBLIC_*` values as browser-exposed; never place secrets in them.
16. Never log passwords, secrets, tokens, database credentials, or sensitive configuration.
17. V1 has no authentication; deployed V1 must remain private/unlisted or use an explicitly approved access gate.

## 4. API Contract Rules

18. **Follow the SRS API contract exactly**: endpoints, HTTP methods, request shapes, response shapes, query parameters, validation rules, and status codes.
19. Use FastAPI/Pydantic schemas as the backend contract and keep OpenAPI/Swagger accurate.
20. Use a centralized typed frontend API client; do not scatter raw API URLs throughout components.
21. Follow the standard API error shape and map backend field errors to the correct frontend fields.
22. Do not make breaking API contract changes without explicit approval and corresponding frontend/test updates.

## 5. Database Rules

23. PostgreSQL is the source of truth for application data.
24. Use **SQLAlchemy 2.0 async + asyncpg** according to the SRS.
25. **Every database schema change must use an Alembic migration. Never manually modify the database schema.**
26. Review generated migrations before applying/committing them.
27. Preserve database constraints, foreign keys, indexes, unique constraints, and deletion rules defined in the SRS.
28. Budget status, remaining balance, and other live calculations must be computed from real database data; do not store derived values when the SRS says they must be calculated at request time.
29. Keep database operations efficient: use pagination, indexes, and SQL-side aggregation where required.

## 6. Data Integrity & Seeding Rules

30. **Never use hardcoded/demo/mock financial data in the frontend or backend.**
31. All expenses, budgets, reports, dashboard values, and charts must come from real API/database data.
32. Only the approved starter categories may be seeded.
33. Never seed expenses or budgets.
34. The seed script must be idempotent and safe to run repeatedly.
35. Empty states must represent a genuinely empty database, not hidden demo data.

## 7. Validation & Business Rules

36. Validate on the frontend with **React Hook Form + Zod** for immediate UX feedback.
37. Validate again on the backend with **Pydantic**; backend validation is authoritative.
38. Never rely only on frontend validation for business-critical constraints.
39. Preserve all SRS rules such as positive amounts, maximum title length, no future expense dates, valid payment modes, and valid category relationships.
40. Prevent duplicate form submissions.
41. Warn users before losing unsaved changes.
42. Destructive operations must require explicit confirmation and follow the SRS conflict/cascade rules.

## 8. Frontend UI/UX Rules

43. Build a production-quality UI, not a basic CRUD interface.
44. Follow mobile-first responsive design across mobile, tablet, laptop, desktop, and large monitors.
45. No unintended horizontal overflow.
46. Every screen must support **empty, loading, error, and retry states** where applicable.
47. Use centralized design tokens for typography, spacing, borders, radii, shadows, and semantic colors.
48. Follow accessibility requirements: semantic HTML, keyboard navigation, visible focus states, appropriate ARIA, and sufficient contrast.
49. Financial/status information must not depend on color alone.
50. Use consistent currency formatting through the centralized currency utility.

## 9. Animation, Micro-Interaction & 3D Rules

51. Use **Framer Motion intentionally**, not excessively.
52. Animations must be short, subtle, non-blocking, and respect `prefers-reduced-motion`.
53. Never delay API/business actions until an animation completes.
54. Use meaningful micro-interactions for loading, success, validation, destructive actions, and important state changes.
55. **3D is optional enhancement only.** It must never affect core functionality or business correctness.
56. Lazy-load 3D/heavy visual modules and provide a fallback when WebGL is unavailable or unsuitable.
57. Never allow animation or 3D to block initial/core content.

## 10. Performance Rules

58. Prefer Next.js Server Components where appropriate; use Client Components only when interactivity requires them.
59. Use TanStack Query for server-state caching, invalidation, loading, and error handling.
60. Avoid duplicate API requests when valid cached data exists.
61. Lazy-load non-critical/heavy modules.
62. Keep charts and dashboard calculations API-driven and efficient.
63. Avoid unnecessary re-renders, oversized assets, layout shifts, and blocking visual effects.
64. Core functionality must remain usable on typical mobile hardware and slow networks.

## 11. Testing & Quality Rules

65. Every feature must be tested before being considered complete.
66. Backend: **Pytest + pytest-asyncio + httpx.AsyncClient**.
67. Frontend: **Vitest + React Testing Library**.
68. E2E: **Playwright** for critical user flows.
69. Test both successful and failure/edge cases.
70. Test with an empty database and real database data.
71. Verify responsive layouts, keyboard navigation, reduced-motion behavior, slow-network behavior, and WebGL fallback.
72. No feature is complete if it only works in the happy path.

## 12. Run → Test → Deploy

73. Follow the PRD's mandatory **Run → Test → Deploy** cycle.
74. Do not move to the next implementation stage while the current stage is broken or untested.
75. Run backend and frontend locally before deployment.
76. Verify database migrations from an empty database.
77. Verify `/api/health` performs a real database connectivity check.
78. Run the complete automated test suite before release.
79. Use GitHub Actions as the quality gate; deploy only from a passing pipeline.
80. Perform production smoke tests after deployment.

## 13. Git & Change-Control Rules

81. **Never directly commit or push changes without asking Om Bhai first.**
82. Before making a commit, show what changed and why.
83. Before pushing, explicitly ask for approval.
84. Keep commits focused and meaningful; avoid unrelated changes.
85. Do not overwrite or delete existing project work without approval.
86. Do not change architecture, dependencies, database schema, API contracts, or major UI behavior without approval.
87. Keep documentation synchronized with approved technical changes.

## 14. Stable V1 Release Gate

88. Stable V1 requires all core CRUD flows to work end-to-end against real PostgreSQL data.
89. All required API endpoints must be implemented and tested.
90. Dashboard, charts, filters, sorting, categories, and budgets must use real API responses.
91. No demo financial data or hardcoded application data may remain.
92. Client and server validation must both pass.
93. Empty/loading/error/retry states must work.
94. Responsive, accessibility, performance, animation, and 3D fallback requirements must be verified.
95. Dockerized local setup must work.
96. Render + Vercel + Supabase connectivity and migrations must be verified if deployed.
97. Production smoke tests must cover:
   - Add → View → Edit → Delete expense
   - Category create → rename → delete/reassign
   - Search → filter → sort
   - Dashboard updates
   - Budget create → update → live status
98. Secrets must be verified absent from Git.
99. GitHub Actions lint/test pipeline must pass.
100. **Do not declare FinTrack “Stable V1” until the complete release gate passes.**
