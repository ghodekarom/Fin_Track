export type InsightCategory =
  | "quick_win"
  | "budget_alert"
  | "subscription"
  | "high_impact";

export interface SpendingInsight {
  id: string;
  type: InsightCategory;
  title: string;
  description: string;
  potential_savings?: number | null;
  action_tip: string;
  impact_level: "high" | "medium" | "low";
}

export interface SpendingInsightsResponse {
  insights: SpendingInsight[];
  total_potential_monthly_savings: number;
  currency: string;
  generated_at: string;
  provider: string;
  is_cached: boolean;
}

// Phase 2: Predictive Overspend & Dynamic Budgeting Types
export type VelocityRiskLevel = "safe" | "moderate" | "critical";

export interface CategoryVelocityForecast {
  category_id: string;
  category_name: string;
  budget_limit: number;
  current_spent: number;
  daily_burn_rate: number;
  projected_month_end_spend: number;
  projected_overage: number;
  exhaustion_day: number | null;
  risk_level: VelocityRiskLevel;
  safe_daily_spend: number;
}

export interface OverallVelocityForecast {
  overall_budget_limit: number | null;
  current_spent: number;
  daily_burn_rate: number;
  projected_month_end_spend: number;
  projected_overage: number;
  days_elapsed: number;
  days_remaining: number;
  safe_daily_spend: number;
  risk_level: VelocityRiskLevel;
  risk_message: string;
  category_forecasts: CategoryVelocityForecast[];
}

export interface DynamicBudgetRecommendation {
  category_id: string;
  category_name: string;
  current_budget: number | null;
  suggested_budget: number;
  average_monthly_spend: number;
  reasoning: string;
}

export interface PredictiveBudgetResponse {
  velocity: OverallVelocityForecast;
  smart_allocations: DynamicBudgetRecommendation[];
  currency: string;
  generated_at: string;
}

// Phase 3: "Ask FinTrack AI" — Conversational Financial Assistant
export type ChatMessageRole = "user" | "assistant";

export interface ChatMessage {
  id?: string;
  role: ChatMessageRole;
  content: string;
  timestamp?: string;
  suggested_followups?: string[];
  provider?: string;
}

export interface AskAiQueryRequest {
  question: string;
  history?: { role: ChatMessageRole; content: string }[];
}

export interface AskAiQueryResponse {
  answer: string;
  related_metrics?: Record<string, any> | null;
  suggested_followups: string[];
  provider: string;
}

// Phase 4: Natural Language Quick-Add Types
export interface ParsedExpenseDraft {
  title: string;
  amount: number;
  category_id?: string | null;
  category_name: string;
  expense_date: string;
  payment_mode: "cash" | "card" | "upi" | "other";
  notes?: string | null;
  confidence_score: number;
  provider: string;
}

export interface QuickAddConfirmRequest {
  title: string;
  amount: number;
  category_id: string;
  expense_date: string;
  payment_mode: "cash" | "card" | "upi" | "other";
  notes?: string | null;
}

// Phase 5: Financial Health Score & Executive Summary Types
export interface ScorePillarBreakdown {
  budget_adherence: number;
  savings_velocity: number;
  category_discipline: number;
}

export interface FinancialHealthScoreResponse {
  health_score: number;
  letter_grade: string;
  status_label: string;
  pillars: ScorePillarBreakdown;
  executive_summary: string;
  key_achievements: string[];
  improvement_goals: string[];
  top_spend_category: string;
  potential_monthly_savings: number;
  period_month: string;
  generated_at: string;
  provider: string;
}
