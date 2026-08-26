export interface CategoryBrief {
  id: string;
  name: string;
}

export interface Category {
  id: string;
  name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  expense_count: number;
}
