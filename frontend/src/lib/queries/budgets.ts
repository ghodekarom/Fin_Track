import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api-client";
import { Budget, BudgetStatus } from "../../types/budget";

export const BUDGETS_QUERY_KEY = ["budgets"];

// Fetch list of budgets configured for a period
export function useBudgets(periodMonth?: string) {
  return useQuery<Budget[], any>({
    queryKey: [...BUDGETS_QUERY_KEY, periodMonth],
    queryFn: async () => {
      const params = periodMonth ? { period_month: periodMonth } : undefined;
      const response = await apiClient.get<Budget[]>("/budgets", { params });
      return response.data;
    },
  });
}

// Fetch live warning status, spent, and remaining details for all budgets
export function useBudgetsStatus(periodMonth?: string) {
  return useQuery<BudgetStatus[], any>({
    queryKey: [...BUDGETS_QUERY_KEY, "status", periodMonth],
    queryFn: async () => {
      const params = periodMonth ? { period_month: periodMonth } : undefined;
      const response = await apiClient.get<BudgetStatus[]>("/budgets/status", { params });
      return response.data;
    },
  });
}

// Create overall or per-category budget goal
export function useCreateBudget() {
  const queryClient = useQueryClient();
  
  return useMutation<Budget, any, Omit<Budget, "id" | "category" | "created_at" | "updated_at">>({
    mutationFn: async (payload) => {
      const response = await apiClient.post<Budget>("/budgets", payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BUDGETS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// Update limit amount of a budget goal
export function useUpdateBudget() {
  const queryClient = useQueryClient();
  
  return useMutation<Budget, any, { id: string; limit_amount: number }>({
    mutationFn: async ({ id, limit_amount }) => {
      const response = await apiClient.put<Budget>(`/budgets/${id}`, { limit_amount });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BUDGETS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// Remove a budget goal
export function useDeleteBudget() {
  const queryClient = useQueryClient();
  
  return useMutation<void, any, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`/budgets/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BUDGETS_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
