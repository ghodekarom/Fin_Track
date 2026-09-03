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
