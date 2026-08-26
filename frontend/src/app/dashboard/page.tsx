"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  useDashboardSummary,
  useMoMComparison,
  useCategoryBreakdown,
  useSpendingTrend,
} from "@/lib/queries/dashboard";
import { useBudgetsStatus } from "@/lib/queries/budgets";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { SpendingTrendChart } from "@/components/dashboard/SpendingTrendChart";
import { CategoryPieChart } from "@/components/dashboard/CategoryPieChart";
import { BudgetStatusCard } from "@/components/dashboard/BudgetStatusCard";
import { BudgetForm } from "@/components/budgets/BudgetForm";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { formatCurrency } from "@/lib/utils/currency";
import { format } from "date-fns";
import { Plus, Eye, Receipt, Calendar, Info, X } from "lucide-react";

export default function Dashboard() {
  const [trendInterval, setTrendInterval] = useState<"daily" | "weekly" | "monthly">("daily");
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);

  // Queries
  const { data: summary, isLoading: sumLoading, isError: sumError, refetch: refetchSum } = useDashboardSummary();
  const { data: mom, isLoading: momLoading } = useMoMComparison();
  const { data: breakdown, isLoading: breakLoading } = useCategoryBreakdown();
  const { data: trend, isLoading: trendLoading } = useSpendingTrend(trendInterval);
  const { data: budgetsStatus, refetch: refetchBudgets } = useBudgetsStatus();

  const handleRetry = () => {
    refetchSum();
    refetchBudgets();
  };

  const handleBudgetSuccess = () => {
    setIsBudgetModalOpen(false);
    refetchSum();
    refetchBudgets();
  };

  if (sumLoading || momLoading) {
    return <LoadingState variant="grid" />;
  }

  if (sumError) {
    return <ErrorState onRetry={handleRetry} />;
  }

  // Find the overall budget from the budgets list
  const overallBudget = budgetsStatus?.find((b) => b.scope === "overall");

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Upper Title and Actions header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Welcome to FinTrack</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Here is a snapshot of your spending patterns and budget status.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsBudgetModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition duration-150 active:scale-95 shrink-0"
          >
            <Plus className="h-4 w-4" />
            Set Budget Target
          </button>
          <Link
            href="/expenses/new"
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-black bg-primary hover:bg-primary/90 rounded-xl transition duration-150 active:scale-95 shrink-0"
          >
            <Plus className="h-4 w-4" />
            Log Expense
          </Link>
        </div>
      </div>

      {/* Row 1: Summary Cards */}
      <SummaryCards
        momComparison={mom}
        overallBudgetStatus={overallBudget}
      />

      {/* Row 2: Charts Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SpendingTrendChart
          data={trend}
          interval={trendInterval}
          onIntervalChange={setTrendInterval}
        />
        <CategoryPieChart data={breakdown} />
      </div>

      {/* Row 3: Recent List and Warning statuses */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Expenses List */}
        <div className="glass-card p-6 rounded-2xl border border-white/5 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
              <Receipt className="h-4 w-4 text-primary" />
              Recent Transactions
            </h2>
            <Link
              href="/expenses"
              className="flex items-center gap-1 text-xs font-semibold text-primary hover:text-primary/95 transition"
            >
              <span>View All Log</span>
              <Eye className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            {summary?.recent_expenses.length === 0 ? (
              <div className="text-center py-8 text-xs text-muted-foreground">
                No expense transactions logged yet. Click "Log Expense" to start.
              </div>
            ) : (
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-white/5 text-[11px] font-bold text-muted-foreground uppercase">
                    <th className="py-2.5">Title</th>
                    <th className="py-2.5">Date</th>
                    <th className="py-2.5">Category</th>
                    <th className="py-2.5 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-neutral-300">
                  {summary?.recent_expenses.map((exp) => (
                    <tr key={exp.id} className="hover:bg-white/1">
                      <td className="py-3 font-semibold text-white max-w-[150px] truncate">{exp.title}</td>
                      <td className="py-3 text-xs text-muted-foreground">
                        {format(new Date(exp.expense_date), "dd MMM")}
                      </td>
                      <td className="py-3">
                        <span className="text-[10px] font-bold tracking-wider px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/5">
                          {exp.category.name}
                        </span>
                      </td>
                      <td className="py-3 text-right font-bold text-white">
                        {formatCurrency(exp.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Budgets Progress Status limits */}
        <div className="lg:col-span-1">
          <BudgetStatusCard
            budgetsStatus={budgetsStatus}
            onAddBudgetClick={() => setIsBudgetModalOpen(true)}
          />
        </div>
      </div>

      {/* Set Budget Modal Overlay */}
      {isBudgetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/75 backdrop-blur-sm" onClick={() => setIsBudgetModalOpen(false)} />
          <div className="relative glass-card border border-white/10 p-6 rounded-3xl w-full max-w-md bg-zinc-950 shadow-2xl">
            <button
              onClick={() => setIsBudgetModalOpen(false)}
              className="absolute top-4 right-4 p-1 rounded-lg bg-white/5 text-muted-foreground hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
            <BudgetForm
              onSuccess={handleBudgetSuccess}
              onCancel={() => setIsBudgetModalOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
