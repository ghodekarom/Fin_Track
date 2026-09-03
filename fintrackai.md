# FinTrack AI Engine — Features & Capabilities

FinTrack integrates an enterprise-grade AI Recommendation & Intelligence Engine powered by Google Gemini with deterministic offline fallbacks. Below are the 5 core AI capabilities implemented:

---

### 1. 💡 Smart Spending Insights & Savings Advisor
* **Description:** Analyzes 30–60 days of personal transactions to detect recurring subscriptions, unnecessary expense spikes, and untapped savings opportunities. Delivers categorized recommendations across Quick Wins, Budget Alerts, Subscriptions, and High-Impact savings with exact rupee-saving estimates.

### 2. 🔮 Predictive Overspend Warning & Dynamic Budget Allocator
* **Description:** Forecasts end-of-month budget exhaustion dates by tracking real-time daily burn rate against safe daily allowances. Includes a 1-click **Dynamic Budget Allocator** that suggests optimal category ceilings based on weighted historical spending.

### 3. 💬 "Ask FinTrack AI" Conversational Assistant
* **Description:** A floating context-aware chatbot grounded strictly in the user's isolated financial ledger. Answers natural-language queries (English & Hinglish) regarding affordability checks (*"Can I afford a ₹5,000 watch?"*), budget limits, recent spending, and subscription audits.

### 4. ⚡ Natural Language Quick-Add & Smart Auto-Categorization
* **Description:** Parses conversational expense logs (e.g., *"Spent 450 on Uber to office yesterday via upi"*) into structured expense drafts. Automatically infers item title, numeric amount, expense date, payment mode, and assigns the correct budget category for 1-click saving.

### 5. 🏆 Monthly Financial Health Score (0–100) & Executive AI Digest
* **Description:** Computes an algorithmic financial health index evaluated across 3 key pillars: Budget Adherence (40 pts), Savings Velocity (35 pts), and Category Discipline (25 pts). Accompanied by a monthly "Spotify-Wrapped" style executive summary, milestones, and strategic goals.

---

### 🛠️ Technology Stack
* **LLM Engine:** Google Gemini API (`gemini-flash-latest` / `gemini-1.5-flash`) via secure REST integration.
* **Resilience:** Deterministic rule-based fallback engines ensuring 100% uptime with zero crashes.
* **Privacy:** Strict per-user isolated data boundaries; zero cross-tenant data leakage.
