"use client";

import React from "react";
import { BudgetStatus } from "../../types/budget";
import { formatCurrency } from "../../lib/utils/currency";
import { useDeleteBudget } from "../../lib/queries/budgets";
import { Scale, ShieldAlert, Trash2, ArrowUpRight } from "lucide-react";
import { EmptyState } from "../ui/EmptyState";

interface BudgetStatusCardProps {
  budgetsStatus?: BudgetStatus[];
  onAddBudgetClick?: () => void;
}

export function BudgetStatusCard({
  budgetsStatus = [],
  onAddBudgetClick,
}: BudgetStatusCardProps) {
  const deleteBudgetMutation = useDeleteBudget();

  const getStatusDetails = (status: string) => {
    switch (status) {
      case "over_budget":
        return {
          label: "Over Budget",
          textClass: "text-red-400",
          bgClass: "bg-red-500",
          borderClass: "border-red-500/20",
          badgeClass: "bg-red-500/10 text-red-400 border-red-500/20",
        };
      case "near_limit":
        return {
          label: "Near Limit",
          textClass: "text-amber-400",
          bgClass: "bg-amber-500",
          borderClass: "border-amber-500/20",
          badgeClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        };
      default:
        return {
          label: "On Track",
          textClass: "text-emerald-400",
          bgClass: "bg-emerald-500",
          borderClass: "border-emerald-500/20",
          badgeClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        };
    }
  };

  const handleDeleteBudget = async (id: string) => {
    if (confirm("Remove this budget limit?")) {
      try {
        await deleteBudgetMutation.mutateAsync(id);
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
      <div className="flex items-center justify-between border-b border-white/5 pb-3">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
          <Scale className="h-4 w-4 text-primary" />
          Budget Limit Trackers
        </h2>
        {onAddBudgetClick && (
          <button
            onClick={onAddBudgetClick}
            className="flex items-center gap-1 text-xs font-semibold text-primary hover:text-primary/95 transition"
          >
            <span>Set Target</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {budgetsStatus.length === 0 ? (
        <EmptyState
          title="No Budgets Active"
          description="Set spending limits overall or for specific categories to monitor indicators here."
          icon={<ShieldAlert className="h-10 w-10 text-muted-foreground/60" />}
          action={
            onAddBudgetClick ? (
              <button
                onClick={onAddBudgetClick}
                className="px-4 py-2 text-xs font-semibold bg-primary text-black rounded-xl hover:bg-primary/90 transition"
              >
                Set a Budget Goal
              </button>
            ) : undefined
          }
        />
      ) : (
        <div className="space-y-6 max-h-[360px] overflow-y-auto pr-1">
          {budgetsStatus.map((budget) => {
            const isOverall = budget.scope === "overall";
            const percent = budget.limit_amount > 0 ? Math.min(100, Math.max(0, (Number(budget.spent) / Number(budget.limit_amount)) * 100)) : 0;
            const statusStyle = getStatusDetails(budget.status);

            return (
              <div key={budget.id} className="space-y-2 border border-white/2 hover:border-white/5 p-4 rounded-2xl bg-white/2 transition">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-sm text-white">
                      {isOverall ? "Overall Monthly Limit" : `${budget.category_name} Limit`}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Spent {formatCurrency(budget.spent)} of {formatCurrency(budget.limit_amount)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border capitalize ${statusStyle.badgeClass}`}>
                      {statusStyle.label}
                    </span>
                    <button
                      onClick={() => handleDeleteBudget(budget.id)}
                      className="p-1 rounded bg-white/5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition"
                      title="Remove limit"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${statusStyle.bgClass}`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                    <span>{percent.toFixed(0)}% Utilized</span>
                    <span>
                      {budget.remaining >= 0
                        ? `${formatCurrency(budget.remaining)} left`
                        : `${formatCurrency(Math.abs(budget.remaining))} over limit`}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
export default BudgetStatusCard;
