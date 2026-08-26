import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api-client";
import { Expense, PaginatedExpenses, PaymentMode } from "../../types/expense";

export const EXPENSES_QUERY_KEY = ["expenses"];

export interface ExpenseFilters {
  search?: string;
  category_id?: string;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  payment_mode?: PaymentMode;
  sort_by?: "amount" | "date" | "category";
  sort_order?: "asc" | "desc";
}

// Fetch list of expenses with pagination and filtering
export function useExpenses(filters: ExpenseFilters, page: number = 1, size: number = 20) {
  return useQuery<PaginatedExpenses, any>({
    queryKey: [...EXPENSES_QUERY_KEY, filters, page, size],
    queryFn: async () => {
      // Map filters to backend query parameters
      const params: Record<string, any> = {
        page,
        size,
        sort_by: filters.sort_by || "date",
        sort_order: filters.sort_order || "desc",
      };

      if (filters.search) params.search = filters.search;
      if (filters.category_id) params.category_id = filters.category_id;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
      if (filters.amount_min !== undefined && filters.amount_min !== null) params.amount_min = filters.amount_min;
      if (filters.amount_max !== undefined && filters.amount_max !== null) params.amount_max = filters.amount_max;
      if (filters.payment_mode) params.payment_mode = filters.payment_mode;

      const response = await apiClient.get<PaginatedExpenses>("/expenses", { params });
      return response.data;
    },
  });
}

// Fetch a single expense by ID
export function useExpense(id: string) {
  return useQuery<Expense, any>({
    queryKey: [...EXPENSES_QUERY_KEY, id],
    queryFn: async () => {
      const response = await apiClient.get<Expense>(`/expenses/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

// Create expense
export function useCreateExpense() {
  const queryClient = useQueryClient();
  
  return useMutation<Expense, any, Omit<Expense, "id" | "category" | "created_at" | "updated_at">>({
    mutationFn: async (payload) => {
      const response = await apiClient.post<Expense>("/expenses", payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });
}

// Update expense
export function useUpdateExpense() {
  const queryClient = useQueryClient();
  
  return useMutation<Expense, any, { id: string; payload: Partial<Omit<Expense, "id" | "category" | "created_at" | "updated_at">> }>({
    mutationFn: async ({ id, payload }) => {
      const response = await apiClient.put<Expense>(`/expenses/${id}`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: [...EXPENSES_QUERY_KEY, variables.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });
}

// Delete expense
export function useDeleteExpense() {
  const queryClient = useQueryClient();
  
  return useMutation<void, any, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`/expenses/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EXPENSES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });
}
