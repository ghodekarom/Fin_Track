import { CategoryBrief } from "./category";

export type PaymentMode = "cash" | "card" | "upi" | "other";

export interface Expense {
  id: string;
  title: string;
  amount: number;
  expense_date: string; // YYYY-MM-DD
  notes: string | null;
  payment_mode: PaymentMode | null;
  category_id: string;
  category: CategoryBrief;
  created_at: string;
  updated_at: string;
}

export interface PaginatedExpenses {
  items: Expense[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
