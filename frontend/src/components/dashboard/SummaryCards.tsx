"use client";

import React from "react";
import { formatCurrency } from "@/lib/utils/currency";
import { MoMComparison, AverageSpend } from "@/lib/queries/dashboard";
import { BudgetStatus } from "@/types/budget";
import { TrendingDown, TrendingUp, DollarSign, Calendar, Scale } from "lucide-react";

interface SummaryCardsProps {
  momComparison?: MoMComparison;
  averageSpend?: AverageSpend;
  overallBudgetStatus?: BudgetStatus;
}

export function SummaryCards({
  momComparison,
  averageSpend,
  overallBudgetStatus,
}: SummaryCardsProps) {
  // Format MoM Comparison percentage
  const renderMoMIndicator = () => {
    if (!momComparison || momComparison.percentage_change === null || momComparison.percentage_change === undefined) {
      return null;
    }
    
    const pct = momComparison.percentage_change;
    const isHigher = pct > 0;
    
    return (
      <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-md ${
        isHigher ? "bg-red-500/10 text-red-400" : "bg-emerald-500/10 text-emerald-400"
      }`}>
        {isHigher ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
        <span>{Math.abs(pct).toFixed(1)}% {isHigher ? "more" : "less"} than last month</span>
      </div>
    );
  };

  // Calculate budget values
  const budgetLimit = overallBudgetStatus?.limit_amount ?? 0;
  const budgetSpent = overallBudgetStatus?.spent ?? 0;
  const budgetRemaining = overallBudgetStatus?.remaining ?? 0;
  const budgetStatusVal = overallBudgetStatus?.status ?? "on_track";
  
  const budgetPercent = budgetLimit > 0 ? Math.min(100, Math.max(0, (budgetSpent / budgetLimit) * 100)) : 0;

  const getBudgetStatusColor = (status: string) => {
    switch (status) {
      case "over_budget":
        return "bg-red-500 text-red-500 border-red-500/30";
      case "near_limit":
        return "bg-amber-500 text-amber-500 border-amber-500/30";
      default:
        return "bg-emerald-500 text-emerald-500 border-emerald-500/30";
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Total Spent Card */}
      <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col justify-between min-h-[140px] relative overflow-hidden group">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              Total Spent (This Month)
            </p>
            <h3 className="text-2xl font-bold text-white mt-2">
              {formatCurrency(momComparison?.current_month_spent ?? 0)}
            </h3>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-muted-foreground group-hover:text-primary transition duration-300">
            <DollarSign className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between">
          {renderMoMIndicator()}
          {!momComparison && <div className="h-4 w-32 bg-white/5 rounded animate-pulse" />}
        </div>
      </div>

      {/* Average Spend Card */}
      <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col justify-between min-h-[140px] relative overflow-hidden group">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              Daily Average Spend
            </p>
            <h3 className="text-2xl font-bold text-white mt-2">
              {formatCurrency(averageSpend?.average_spent ?? 0)}
            </h3>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-muted-foreground group-hover:text-primary transition duration-300">
            <Calendar className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-4 text-xs text-muted-foreground font-semibold">
          Calculated for the current month so far
        </div>
      </div>

      {/* Remaining Budget Card */}
      <div className="glass-card p-6 rounded-2xl border border-white/5 flex flex-col justify-between min-h-[140px] relative overflow-hidden group">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">
              Remaining Budget
            </p>
            <h3 className="text-2xl font-bold text-white mt-2">
              {budgetLimit > 0 ? formatCurrency(budgetRemaining) : "No Target Set"}
            </h3>
          </div>
          <div className="p-3 rounded-xl bg-white/5 border border-white/5 text-muted-foreground group-hover:text-primary transition duration-300">
            <Scale className="h-5 w-5" />
          </div>
        </div>
        
        {budgetLimit > 0 ? (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-muted-foreground">Spent {budgetPercent.toFixed(0)}%</span>
              <span className={getBudgetStatusColor(budgetStatusVal).split(" ")[1]}>
                {budgetStatusVal.replace("_", " ")}
              </span>
            </div>
            <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  budgetPercent >= 100
                    ? "bg-red-500"
                    : budgetPercent >= 80
                    ? "bg-amber-500"
                    : "bg-primary"
                }`}
                style={{ width: `${budgetPercent}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="mt-4 text-xs text-muted-foreground font-semibold">
            Define a monthly spending target to track remaining balance
          </div>
        )}
      </div>
    </div>
  );
}
export default SummaryCards;
