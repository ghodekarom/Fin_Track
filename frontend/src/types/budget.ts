import { CategoryBrief } from "./category";

export type BudgetScope = "overall" | "category";

export interface Budget {
  id: string;
  scope: BudgetScope;
  category_id: string | null;
  category: CategoryBrief | null;
  period_month: string; // YYYY-MM-DD (typically first of month)
  limit_amount: number;
  created_at: string;
  updated_at: string;
}

export type BudgetStatusType = "on_track" | "near_limit" | "over_budget";

export interface BudgetStatus {
  id: string;
  scope: BudgetScope;
  category_id: string | null;
  category_name: string | null;
  period_month: string;
  limit_amount: number;
  spent: number;
  remaining: number;
  status: BudgetStatusType;
}
