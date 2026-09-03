# Product Requirements Document (PRD)
## FinTrack — Personal Expense Tracker

---

## 1. Overview / Introduction

**Product Name:** FinTrack

**Summary:** FinTrack is a personal finance web app that lets a user log daily expenses, organize them into self-created categories, and instantly see the impact on totals, charts, and a live budget — turning scattered notes/spreadsheet habits into one simple, searchable place to track spending.

---

## 2. Problem Statement

Most people don't track their expenses properly. They either forget to log them, or rely on tools like notes apps and spreadsheets that are hard to search, filter, or understand at a glance.

Because of this, they can't easily answer three simple questions:
- "How much have I spent?"
- "Where is my money going?"
- "Am I within my budget, or over it?"

FinTrack solves this by giving the user one simple place to log expenses and instantly see the impact on their total spending and budget.

---

## 3. Why Keep V1 (MVP) Small?

V1 focuses only on the core loop:

> **Log an expense → See it reflected in totals & charts → Track budget left**

Everything else (login, recurring expenses, notifications, multi-user support, bank sync, multi-currency) is left for later phases. This keeps V1 simple to build, easy to test, and easy to actually use.

---

## 4. Goals

| Goal | Why It Matters |
|------|------------------|
| Add an expense in under 30 seconds | Easy logging = user actually keeps using it |
| Show spending visually | Helps the user understand "where money is going" without extra effort |
| Show a live remaining budget | Turns tracking into real budgeting, not just note-taking |
| Make old expenses easy to find | A log is useless if you can't search or filter it later |
| Build a scalable foundation | Later phases (Section 13) should not require rebuilding the core |

**Success Metrics:**
- Number of expenses logged per active user per week
- % of users who set a budget goal
- Time taken to add a single expense (target: under 30 seconds)
- Search/filter usage frequency
- User retention after 30 days

---

## 5. Target Audience

**Who this is for:**
- One person who wants to manually track their own personal spending
- Budget-conscious users trying to control overspending
- Users who want visual/report-based insight into where their money goes

**Not for (V1):**
- Teams or families sharing one account
- Businesses
- Advanced investment/finance tracking

---

## 6. Scope (V1 / MVP with Secure Authentication)

**✅ In-Scope:**
- **User Authentication & Accounts:**
  - Secure Sign Up / Registration (Email & Password)
  - Secure Login / Sign In (Email & Password)
  - One-click Google Sign-In (OAuth 2.0 / OpenID Connect)
  - Secure Logout (current device and logout from all devices/sessions)
  - Forgot Password & Password Reset via email
  - Change Password from user settings
- **User Data Isolation (Strict Privacy):**
  - Complete data privacy: every user only accesses, manages, and views their own personal expenses, categories, and budgets.
  - Zero cross-user visibility or tampering.
- **Expense Tracking & Management:**
  - Full CRUD on expenses (Add / View / Edit / Delete)
  - Categories the user creates and manages themselves (plus starter categories)
  - Dashboard with total spend + charts (pie/donut + bar/line)
  - Search, filter, and sort on expenses (usable together)
  - Budget goal setting (overall + per-category) with live remaining-balance tracking
  - Simple, responsive navigation (Dashboard, Expenses, Categories, Budgets, User Profile/Logout)
  - Field validation (positive amount, no future-dated expenses, strong password requirements)
  - Empty, loading, and error states for all screens
  - Single fixed currency display (₹ / INR, 2 decimal places)

**❌ Out-of-Scope:**
- Admin roles / Role-Based Access Control (RBAC) — every user is a peer with access only to their own personal data
- Recurring or auto-scheduled expenses
- Multiple currencies
- Bank / UPI / SMS auto-import
- Income tracking
- Report export (PDF/Excel/CSV) — nice-to-have only if time permits, otherwise Phase 3
- Dedicated native mobile app (responsive web app / PWA with offline support)

---

## 7. Functional Requirements & User Stories

### 7.0 User Accounts & Authentication

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-0.1 | **Sign Up / Register** | P0 | As a new user, I want to create an account with my email and password so my financial data is securely saved. |
| FR-0.2 | **Login / Sign In** | P0 | As a returning user, I want to sign in with my credentials to access my personal financial records. |
| FR-0.3 | **Sign in with Google** | P0 | As a user, I want to sign in with my Google account with one click for fast and easy access. |
| FR-0.4 | **Logout** | P0 | As a user, I want to log out of my account securely so nobody else using my browser can view my financial logs. |
| FR-0.5 | **Logout All Devices** | P1 | As a user, I want an option to sign out of all active sessions across all devices for security. |
| FR-0.6 | **Forgot & Reset Password** | P0 | As a user who forgot their password, I want to receive a secure password reset link by email to regain account access. |
| FR-0.7 | **Change Password** | P1 | As an authenticated user, I want to update my password from my account settings. |
| FR-0.8 | **User Data Isolation** | P0 | As a user, I want complete privacy so that only I can see, edit, or delete my expenses, categories, and budgets, and no other user can ever access or tamper with my data. |

### 7.1 Navigation

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-1 | Responsive navigation menu with sections: **Dashboard**, **Expenses**, **Categories**, **Budgets**, and **Account / Logout** | P0 | As a user, I want clear navigation so I can move between sections and manage my account easily. |

### 7.2 Expense Fields & Validation

When adding an expense, the user fills in:
- **Title** — short description (e.g. "Groceries")
- **Category** — dynamic; pick an existing one or create a new one
- **Amount** — how much was spent (displayed as ₹ with 2 decimal places, e.g. ₹1,234.00)
- **Date** — defaults to today, can be changed
- **Notes** (optional) — any extra detail
- **Payment Mode** (optional) — e.g. Cash, Card, UPI, Other

| Validation Rule | Why |
|------------------|-----|
| Amount must be a positive number | Prevents bad data from skewing totals and charts |
| Date cannot be in the future | Keeps the log honest to actual spending |
| Title is required, max 50 characters | Keeps expense list scannable |

### 7.3 Expense CRUD

| ID | Action | Description | Priority | User Story |
|----|--------|--------------|----------|------------|
| FR-2 | Add | Create a new expense entry linked to the logged-in user | P0 | As a user, I want to quickly add an expense so that logging spending doesn't feel like a chore. |
| FR-3 | View | See all logged expenses belonging only to the logged-in user in a paginated list | P0 | As a user, I want to view my past expenses so I can review my spending history. |
| FR-4 | Edit | Update any field of the user's own existing expense | P0 | As a user, I want to edit my past expenses so my records stay accurate. |
| FR-5 | Delete | Remove the user's own expense, with a confirmation step | P0 | As a user, I want to delete an expense (with confirmation) so I don't lose data by accident. |

### 7.4 Category Management

Categories are dynamic — users have starter categories and can build their own custom categories.

| ID | Action | Description | Priority | User Story |
|----|--------|--------------|----------|------------|
| FR-6 | Create | Add a new user-scoped category by name | P0 | As a user, I want to create my own categories so my spending is organized the way I actually think about it. |
| FR-7 | Edit | Rename a user's category | P0 | As a user, I want to rename a category so I can keep my organization consistent over time. |
| FR-8 | Delete | Remove a category safely (reassign expenses or cascade with confirmation) | P0 | As a user, I want to safely delete a category without accidentally losing or orphaning expense data. |
| FR-9 | View | See user's active categories and linked expense counts | P1 | As a user, I want to see how many expenses are in each category so I understand my category usage. |
| FR-10 | Default Categories | Ship with common starter categories (Food, Transport, Rent, etc.) for new accounts | P2 | As a new user, I want to see some starter categories so the app feels usable from day one. |

### 7.5 Search, Filter & Sort

On the Expenses screen, all capabilities below work together on the user's personal expenses:

| ID | Capability | Details | Priority | User Story |
|----|------------|---------|----------|------------|
| FR-11 | Search | By title or notes text | P1 | As a user, I want to search my expenses by title or note so I can quickly find a specific transaction. |
| FR-12 | Filter — Date Range | e.g. this week, this month, custom range | P0 | As a user, I want to filter expenses by date range so I can review a specific period. |
| FR-13 | Filter — Category | Isolate spend on a specific category | P0 | As a user, I want to filter by category so I can see how much I spent in one area. |
| FR-14 | Filter — Amount Range | Narrow down to a spend bracket | P1 | As a user, I want to filter by amount range so I can find larger or smaller transactions. |
| FR-15 | Filter — Payment Mode | Separate cash vs card vs UPI spend | P1 | As a user, I want to filter by payment mode so I can see how I paid for things. |
| FR-16 | Sort | By amount, date, or category | P1 | As a user, I want to sort my expenses so I can quickly scan the highest, most recent, or grouped entries. |

### 7.6 Dashboard

| ID | Requirement | Why | Priority | User Story |
|----|-------------|-----|----------|------------|
| FR-17 | Total amount spent (overall, and current month by default) | The single most-asked question: "how much did I spend?" | P0 | As a user, I want to see my total spend so I immediately know where I stand. |
| FR-18 | Quick view of recent expenses | Snapshot without opening the full list | P0 | As a user, I want to see my recent expenses on the dashboard so I don't need to open the full list every time. |
| FR-19 | Pie/donut chart — spending by category | Instantly shows where money is going | P0 | As a user, I want to see a category breakdown chart so I know where my money is going. |
| FR-20 | Bar/line chart — spending over time | Reveals patterns and spikes across days/months | P0 | As a user, I want to see my spending trend over time so I can spot patterns or spikes. |
| FR-21 | Budget status vs goal | Turns the dashboard into a budgeting tool, not just a log | P0 | As a user, I want to see my budget status on the dashboard so I know if I'm on track. |
| FR-22 | Daily/Weekly/Monthly report views | Lets the user analyze spending across different time periods | P0 | As a user, I want to view my expenses broken down by day, week, and month so I can analyze my habits over different periods. |
| FR-23 | Month-over-month comparison with % change | Tells the user if they're improving or not | P1 | As a user, I want to compare this month to last month so I know if I'm improving. |
| FR-24 | Top categories by spend, ranked | Surfaces the biggest spending areas without digging | P1 | As a user, I want to see my top spending categories so I know where to cut back. |
| FR-25 | Average daily/weekly spend | Gives a normalized sense of spending pace | P2 | As a user, I want to see my average spend so I can gauge my daily/weekly pace. |

### 7.7 Budget / Spending Goal

The user can set personal spending goals (overall or category-specific):
- Total spent so far in that period
- Remaining budget = Goal − Spent
- A simple status: **on track / near limit / over budget**

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-26 | Set overall monthly budget goal and per-category budget limits | P0 | As a user, I want to set a budget goal so I can catch overspending early. |
| FR-27 | Live remaining-balance tracking as expenses are added | P0 | As a user, I want to see my remaining budget update live as I add expenses so I always know where I stand. |
| FR-28 | Alert/status indicator when nearing or exceeding a limit | P1 | As a user, I want to be warned when I'm close to or over a budget limit so I can adjust my spending in time. |

### 7.8 Data Export (Nice-to-Have)

| ID | Requirement | Why | Priority | User Story |
|----|-------------|-----|----------|------------|
| FR-29 | Export personal expenses as CSV/PDF/Excel | Backup and analysis outside the app | P2 | As a user, I want to export my expenses so I can back them up or analyze them outside the app. |

### 7.9 Data Integrity & Privacy Principle

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-30 | Live Data & Absolute Isolation — All data is securely bound to the authenticated user with zero cross-user access or mock financial data | P0 | As a user, I want full assurance that my financial data is real, private, and inaccessible to any other user. |

### 7.10 AI Recommendation: Monthly Financial Health Score & Executive Summary

The application provides an automated, AI-powered financial advisor experience tailored strictly to the user's spending habits:

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-31 | **Financial Health Score (0–100):** Real-time algorithmically computed rating based on budget adherence, spending velocity, category diversification, and expense control. | P1 | As a user, I want a clear numerical score and status badge (e.g., "Excellent - 88/100") on my dashboard so I immediately know how healthy my financial habits are this month. |
| FR-32 | **Monthly AI Executive Summary:** LLM-generated monthly report card summarizing top spending areas, biggest expenses, and month-over-month trends. | P1 | As a user, I want an easy-to-read summary of my month's finances so I can understand my spending without manually crunching numbers. |
| FR-33 | **Personalized AI Savings Recommendations:** 2–3 actionable, concrete financial tips for the upcoming month to cut costs and improve budget adherence. | P1 | As a user, I want specific recommendations (e.g., "Cap dining out to save ₹3,000 next month") so I know exactly what actions to take. |
| FR-34 | **Exportable / Shareable Monthly Digest:** 1-click clean export/view of the monthly financial performance summary card. | P2 | As a user, I want to download or view a clean summary card of my monthly progress so I can reflect on my financial milestones. |

---

## 8. Key User Flows

| Flow | Steps |
|------|-------|
| 🟢 Sign Up / Login | Open App → Register or Sign in (Password or Google) → Lands on personal Dashboard |
| 🟢 Add an Expense | Expenses → Add New → Fill form (pick/create category) → Save → Appears in list, dashboard updates |
| 🟢 Check Spending & Budget | Dashboard → View personal total spent, charts, recent logs, and budget alerts |
| 🟢 Manage Categories & Budgets | Create/rename/delete custom categories, configure monthly limits |
| 🟢 Password Recovery | Forgot Password → Enter email → Click reset link from email → Set new password → Login |
| 🟢 Secure Logout | User profile menu → Logout (or Logout from all devices) → Session cleared, redirect to login |

---

## 9. Non-Functional Requirements

- **Security & Privacy:**
  - Industry-standard password hashing (BCrypt / Argon2). No plaintext passwords stored.
  - Modern token security (short-lived access tokens, secure rotated refresh cookies).
  - Secure session revocation and logout from all devices.
  - Rate limiting on authentication endpoints to prevent brute-force attacks.
  - Strict user-level data isolation on every action.
- **Performance:** Sub-second response times for dashboard, filters, and reports with real database data.
- **Scalability:** Stateless backend architecture with horizontal scalability.
- **Data Integrity:** Real, user-owned data only. No hardcoded or demo data.
- **Testability & Reliability:** Full test coverage across authentication, authorization isolation, and financial CRUD operations before deployment.

---

## 10. Definition of Done

- User can register, login, sign in with Google, reset password, and securely log out.
- User data is completely isolated: User A cannot see, edit, or delete User B's data under any condition.
- User can Add, View, Edit, and Delete expenses.
- User can create, edit, and delete custom categories.
- User can set budget goals and monitor live remaining balance with warning alerts.
- Dashboard renders accurate charts and summaries based strictly on the logged-in user's data.
- Automated tests pass for authentication, authorization, and core expense workflows.
- Deployed and verified on production environments with HTTPS and secure cookie handling.
