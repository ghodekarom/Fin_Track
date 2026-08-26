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

## 6. Scope (V1 / MVP)

**✅ In-Scope (V1):**
- Full CRUD on expenses (Add / View / Edit / Delete)
- Categories the user creates and manages themselves (not a fixed list)
- Dashboard with total spend + charts (pie/donut + bar/line)
- Search, filter, and sort on expenses (usable together)
- Budget goal setting (overall + per-category) with live remaining-balance tracking
- Simple navigation (hamburger menu: Dashboard, Expenses)
- Field validation (positive amount, no future-dated expenses)
- Empty, loading, and error states for all screens
- Single fixed currency display (₹ / INR, 2 decimal places)

**❌ Out-of-Scope (V1):**
- Login / multiple user accounts
- Recurring or auto-scheduled expenses
- Multiple currencies
- Bank / UPI / SMS auto-import
- Income tracking
- Notifications / reminders
- Report export (PDF/Excel/CSV) — nice-to-have only if time permits, otherwise Phase 2
- Dedicated mobile app (V1 is a responsive web app only — usable on mobile browsers, not a native app)

*(These move into later phases — see Section 13.)*

---

## 7. Functional Requirements & User Stories

### 7.1 Navigation

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-1 | Hamburger menu with two sections: **Dashboard** (view-only summary) and **Expenses** (add/edit/delete/search/filter/sort) | P0 | As a user, I want a simple hamburger menu so I can move between my Dashboard and my Expenses easily. |

### 7.2 Expense Fields & Validation

When adding an expense, the user fills in:
- **Title** — short description (e.g. "Groceries")
- **Category** — dynamic; pick an existing one or create a new one
- **Amount** — how much was spent (displayed as ₹ with 2 decimal places, e.g. ₹1,234.00)
- **Date** — defaults to today, can be changed
- **Notes** (optional) — any extra detail
- **Payment Mode** (optional) — e.g. Cash, Card, UPI

| Validation Rule | Why |
|------------------|-----|
| Amount must be a positive number | Prevents bad data from skewing totals and charts |
| Date cannot be in the future | Keeps the log honest to actual spending |
| Title is required, max 50 characters | Keeps expense list scannable |

### 7.3 Expense CRUD

| ID | Action | Description | Priority | User Story |
|----|--------|--------------|----------|------------|
| FR-2 | Add | Create a new expense entry | P0 | As a user, I want to quickly add an expense so that logging spending doesn't feel like a chore. |
| FR-3 | View | See all logged expenses in a paginated list | P0 | As a user, I want to view my past expenses so I can review my spending history. |
| FR-4 | Edit | Update any field of an existing expense | P0 | As a user, I want to edit my past expenses so my records stay accurate. |
| FR-5 | Delete | Remove an expense, with a confirmation step to avoid deleting by mistake | P0 | As a user, I want to delete an expense (with confirmation) so I don't lose data by accident. |

### 7.4 Category Management

Categories are dynamic — the user builds their own list instead of picking from a fixed set.

| ID | Action | Description | Priority | User Story |
|----|--------|--------------|----------|------------|
| FR-6 | Create | Add a new category by name while logging an expense, or from a category list | P0 | As a user, I want to create my own categories so my spending is organized the way I actually think about it. |
| FR-7 | Edit | Rename an existing category | P0 | As a user, I want to rename a category so I can keep my organization consistent over time. |
| FR-8 | Delete | Remove a category — only if unused, or reassign/cascade linked expenses with a warning | P0 | As a user, I want to safely delete a category without accidentally losing or orphaning expense data. |
| FR-9 | View | See the list of categories along with how many expenses use each one | P1 | As a user, I want to see how many expenses are in each category so I understand my category usage. |
| FR-10 | Default Categories | Ship with a few common starter categories (Food, Transport, Rent, etc.) so the app isn't empty on first use | P2 | As a new user, I want to see some starter categories so the app feels usable from day one. |

### 7.5 Search, Filter & Sort

On the Expenses screen, all capabilities below should work together (e.g. filter by "Food" category, then sort by highest amount).

| ID | Capability | Details | Priority | User Story |
|----|------------|---------|----------|------------|
| FR-11 | Search | By title or notes text | P1 | As a user, I want to search my expenses by title or note so I can quickly find a specific transaction. |
| FR-12 | Filter — Date Range | e.g. this week, this month | P0 | As a user, I want to filter expenses by date range so I can review a specific period. |
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

The user can set a spending goal (e.g. a monthly limit, or a per-category limit). The app automatically shows:
- Total spent so far in that period
- Remaining budget = Goal − Spent
- A simple status: **on track / near limit / over budget**

The user can update the goal anytime, and everything updates instantly.

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-26 | Set an overall monthly budget goal and per-category budget limits | P0 | As a user, I want to set a budget goal so I can catch overspending early. |
| FR-27 | Live remaining-balance tracking as expenses are added | P0 | As a user, I want to see my remaining budget update live as I add expenses so I always know where I stand. |
| FR-28 | Alert/status indicator when nearing or exceeding a limit | P1 | As a user, I want to be warned when I'm close to or over a budget limit so I can adjust my spending in time. |

*Why this matters: this turns the app from "just a log" into a real budgeting tool — this is the heart of V1.*

### 7.8 Data Export (Nice-to-Have)

| ID | Requirement | Why | Priority | User Story |
|----|-------------|-----|----------|------------|
| FR-29 | Export expenses (filtered or full) as CSV/PDF/Excel | Backup and analysis outside the app | P2 | As a user, I want to export my expenses so I can back them up or analyze them outside the app. |

### 7.9 Data Integrity Principle

| ID | Requirement | Priority | User Story |
|----|-------------|----------|------------|
| FR-30 | No hardcoded/demo data at any stage — all data is dynamically created, stored, and fetched from the real data layer (see Section 9) | P0 | As a new user, I want to see an honest empty state built from real, dynamically generated data, so the app reflects my actual usage from day one. |

---

## 8. Key User Flows

| Flow | Steps |
|------|-------|
| 🟢 Add an expense | Expenses → Add New → Fill form (pick or create a category) → Save → Expense appears in list, dashboard totals update |
| 🟢 Check spending | Dashboard → See total spent, charts, and budget status |
| 🟢 Find a past expense | Expenses → Search / Filter / Sort → Find it → Edit or Delete |
| 🟢 Set a budget goal | Set spending limit → Dashboard shows remaining balance, updates live as expenses are added |

---

## 9. Non-Functional Requirements

- **Performance:** Dashboard and reports must load with real, database-driven data (no hardcoded/static values) at any data volume.
- **Scalability:** Architecture should support later phases (Section 13) without major rework.
- **Data Integrity:** No hardcoded or dummy data in any phase — see Section 9.1.
- **Testability:** Every feature/module must be independently testable before deployment.
- **Reliability:** Each phase must be fully functional (run → test → deploy) before the next phase begins.
- **Deployment (V1):** Local or private deployment — no public internet exposure planned for V1, since there is no login/auth layer yet.

### 9.1 Development Principle (Applies to All Phases)

> **No hardcoded/dummy data in any phase.** All data (expenses, categories, budgets, reports) must be dynamically created, stored, and fetched from the actual data layer (database/API), even in early phases. Every phase must independently follow the **Run → Test → Deploy** cycle before moving to the next phase.

---

## 10. Definition of Done (V1)

- User can Add, View, Edit, and Delete expenses
- Categories are dynamic — user can create, edit, and delete their own
- Dashboard shows total spend, a recent-expenses snapshot, and at least 2 charts
- Expenses section supports search + at least 2 filters + at least 2 sort options, usable together
- User can set a budget goal and see a live remaining balance with status (on track/near limit/over budget)
- Hamburger menu navigation works between Dashboard and Expenses
- Amount and date fields are validated (positive amount, no future dates)
- No hardcoded/demo data anywhere in the app — all data is live and dynamic
- Deployed and tested end-to-end before moving to Phase 2

---

## 11. Assumptions & Risks

**Assumptions:**
- Single-user app in V1 — no login needed
- One fixed currency (e.g. INR) — no multi-currency support in V1
- Budget goal defaults to monthly
- Expense date should be today or earlier (not future-dated)
- Local or private deployment for V1 (no public internet exposure)

**Risks:**
- Scope creep if later-phase features get pulled into V1
- Data accuracy risk if hardcoded/test data isn't fully replaced with real data before deployment
- Security risk with financial data once login/multi-device sync is introduced, if auth isn't properly tested each phase

---

## 12. Stakeholders

- Product Owner
- Development Team
- QA/Testing Team
- End Users (primary feedback source for each phase)

---

## 13. Future Scope — Phase-wise Roadmap

| Phase | Theme | Features | Run-Test-Deploy Requirement |
|-------|-------|----------|------------------------------|
| **Phase 1 (V1 / MVP)** | Core Loop | Full expense CRUD, dynamic categories, dashboard with charts, search/filter/sort, budget goal with live balance, hamburger navigation | Build with live data layer, unit + integration test, deploy as standalone working app |
| **Phase 2** | Login, Sync & Convenience | Login & multi-device sync, income tracking, recurring expenses (rent, subscriptions, EMI), receipt photo upload, multiple wallets/accounts (cash, bank, card), report export (PDF/Excel/CSV), dark mode | Each feature tested against real stored data, deployed as an update to Phase 1 app |
| **Phase 3** | Social/Sharing | Split expenses (roommates/friends), shared budgets, multi-user/family accounts | Multi-user data flow tested for accuracy before deployment |
| **Phase 4** | Smart & Advanced | Savings goals, multi-currency support, AI-based spend prediction, auto-categorization, bank/UPI/SMS auto-import, budget notifications, calendar heatmap of spend, year-view trends | AI/ML and integration modules tested independently, then deployed with monitoring |
| **Phase 5** | Security & Personalization | Biometric lock, cloud backup, custom themes, reminders/notifications | Security features tested for edge cases (failed auth, sync conflicts) before deployment |
| **Phase 6** | Monetization | Free vs Premium plans, ads (free tier) | Payment/subscription flow tested in sandbox before production deployment |

---

## 14. Dependencies

- Database/backend for persistent storage of expenses, categories, budgets
- Charting library for dashboard visualizations (pie/donut + bar/line)
- Authentication mechanism (introduced Phase 2 onward — PIN, later biometric)
- Export library for CSV/PDF/Excel (Phase 1 nice-to-have, full in Phase 2)
- Notification system (budget alerts, reminders — Phase 5)
- Payment gateway (Phase 6, for premium plans)

---

## 15. Timeline (Illustrative — to be finalized with dev team)

| Phase | Estimated Duration |
|-------|----------------------|
| Phase 1 (V1 / MVP) | To be defined based on team capacity |
| Phase 2 | To be defined post Phase 1 review |
| Phase 3 | To be defined post Phase 2 review |
| Phase 4 | To be defined post Phase 3 review |
| Phase 5 | To be defined post Phase 4 review |
| Phase 6 | To be defined post Phase 5 review |

*Note: Each phase's timeline should only be finalized after the previous phase is successfully run, tested, and deployed.*
