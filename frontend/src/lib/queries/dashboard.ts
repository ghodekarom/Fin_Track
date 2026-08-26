import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api-client";
import { Expense } from "../../types/expense";
import { BudgetStatus } from "../../types/budget";

export const DASHBOARD_QUERY_KEY = ["dashboard"];

export interface DashboardSummary {
  total_spent: number;
  recent_expenses: Expense[];
  budgets_status: BudgetStatus[];
}

export interface CategoryBreakdown {
  category_id: string | null;
  category_name: string;
  total_spent: number;
  percentage: number;
}

export interface SpendingTrend {
  date: string | null; // YYYY-MM-DD
  total_spent: number;
}

export interface MoMComparison {
  current_month_spent: number;
  previous_month_spent: number;
  percentage_change: number | null;
}

export interface TopCategory {
  category_id: string | null;
  category_name: string;
  total_spent: number;
}

export interface PaymentModeBreakdown {
  payment_mode: string;
  total_spent: number;
  percentage: number;
}

export interface AverageSpend {
  average_spent: number;
  current_month_spent: number;
  basis: string; // "daily" | "weekly"
}

// Fetch dashboard summary
export function useDashboardSummary(periodMonth?: string) {
  return useQuery<DashboardSummary, any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "summary", periodMonth],
    queryFn: async () => {
      const params = periodMonth ? { period_month: periodMonth } : undefined;
      const response = await apiClient.get<DashboardSummary>("/dashboard/summary", { params });
      return response.data;
    },
  });
}

// Fetch category spending breakdown
export function useCategoryBreakdown(dateFrom?: string, dateTo?: string) {
  return useQuery<CategoryBreakdown[], any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "charts", "category-breakdown", dateFrom, dateTo],
    queryFn: async () => {
      const params: Record<string, any> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      
      const response = await apiClient.get<CategoryBreakdown[]>("/dashboard/charts/category-breakdown", { params });
      return response.data;
    },
  });
}

// Fetch spending trend over time
export function useSpendingTrend(period: "daily" | "weekly" | "monthly" = "daily", dateFrom?: string, dateTo?: string) {
  return useQuery<SpendingTrend[], any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "charts", "spending-trend", period, dateFrom, dateTo],
    queryFn: async () => {
      const params: Record<string, any> = { period };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      
      const response = await apiClient.get<SpendingTrend[]>("/dashboard/charts/spending-trend", { params });
      return response.data;
    },
  });
}

// Fetch periodic report breakdown
export function useReportsBreakdown(period: "daily" | "weekly" | "monthly" = "monthly") {
  return useQuery<SpendingTrend[], any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "reports", period],
    queryFn: async () => {
      const response = await apiClient.get<SpendingTrend[]>("/dashboard/reports", { params: { period } });
      return response.data;
    },
  });
}

// Fetch month-over-month total spending comparison
export function useMoMComparison() {
  return useQuery<MoMComparison, any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "comparison"],
    queryFn: async () => {
      const response = await apiClient.get<MoMComparison>("/dashboard/comparison");
      return response.data;
    },
  });
}

// Fetch top categories sorted by spending
export function useTopCategories(limit: number = 5) {
  return useQuery<TopCategory[], any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "top-categories", limit],
    queryFn: async () => {
      const response = await apiClient.get<TopCategory[]>("/dashboard/top-categories", { params: { limit } });
      return response.data;
    },
  });
}

// Fetch average spend rate
export function useAverageSpend(basis: "daily" | "weekly" = "daily") {
  return useQuery<AverageSpend, any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "average-spend", basis],
    queryFn: async () => {
      const response = await apiClient.get<AverageSpend>("/dashboard/average-spend", { params: { basis } });
      return response.data;
    },
  });
}

// Fetch payment mode spending breakdown
export function usePaymentModeBreakdown(dateFrom?: string, dateTo?: string) {
  return useQuery<PaymentModeBreakdown[], any>({
    queryKey: [...DASHBOARD_QUERY_KEY, "charts", "payment-mode-breakdown", dateFrom, dateTo],
    queryFn: async () => {
      const params: Record<string, any> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const response = await apiClient.get<PaymentModeBreakdown[]>("/dashboard/charts/payment-mode-breakdown", { params });
      return response.data;
    },
  });
}
