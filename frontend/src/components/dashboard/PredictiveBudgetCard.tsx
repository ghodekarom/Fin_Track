"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Clock,
  Zap,
  Check,
  Loader2,
  RefreshCw,
  Sparkles,
  Layers,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { PredictiveBudgetResponse, VelocityRiskLevel } from "@/types/ai";

export default function PredictiveBudgetCard({ onBudgetApplied }: { onBudgetApplied?: () => void }) {
  const [data, setData] = useState<PredictiveBudgetResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"velocity" | "allocator">("velocity");
  const [applyingCategoryId, setApplyingCategoryId] = useState<string | null>(null);
  const [appliedCategorySuccess, setAppliedCategorySuccess] = useState<string | null>(null);

  const fetchForecast = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<PredictiveBudgetResponse>("/ai/predictive-budget");
      setData(res.data);
    } catch (err: any) {
      setError(
        err?.message ||
        err?.response?.data?.error?.message ||
        "Could not load predictive forecast right now."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, []);

  const handleApplyBudget = async (categoryId: string, amount: number) => {
    setApplyingCategoryId(categoryId);
    setAppliedCategorySuccess(null);
    try {
      await apiClient.post("/ai/predictive-budget/apply", {
        category_id: categoryId,
        amount,
      });
      setAppliedCategorySuccess(categoryId);
      // Refresh forecast and notify parent dashboard
      await fetchForecast();
      if (onBudgetApplied) {
        onBudgetApplied();
      }
      setTimeout(() => {
        setAppliedCategorySuccess(null);
      }, 3000);
    } catch (err: any) {
      alert(err?.message || "Failed to apply budget limit.");
    } finally {
      setApplyingCategoryId(null);
    }
  };

  const getRiskBannerStyle = (level: VelocityRiskLevel) => {
    switch (level) {
      case "critical":
        return {
          bg: "bg-gradient-to-r from-rose-950/40 via-rose-900/20 to-card border-rose-500/30",
          text: "text-rose-400",
          icon: <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />,
        };
      case "moderate":
        return {
          bg: "bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-card border-amber-500/30",
          text: "text-amber-400",
          icon: <Clock className="w-5 h-5 text-amber-400 shrink-0" />,
        };
      case "safe":
      default:
        return {
          bg: "bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-card border-emerald-500/30",
          text: "text-emerald-400",
          icon: <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />,
        };
    }
  };

  return (
    <div className="relative overflow-hidden bg-card/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl transition-all duration-300">
      {/* Background Decorative Glow */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-56 h-56 rounded-full bg-cyan-500/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-56 h-56 rounded-full bg-emerald-500/5 blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/20 via-blue-500/20 to-emerald-500/20 border border-cyan-500/30 text-cyan-400 shadow-md shadow-cyan-500/10">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-foreground tracking-tight">
                Predictive Overspend & Dynamic Budgeting
              </h2>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/25">
                Velocity AI
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Real-time daily burn rate, exhaustion prediction, and smart budget allocator
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={fetchForecast}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all disabled:opacity-50 cursor-pointer"
            title="Recalculate velocity"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-cyan-400" : ""}`} />
            <span>{isLoading ? "Calculating..." : "Recalculate"}</span>
          </button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5 animate-pulse h-20" />
            ))}
          </div>
          <div className="h-16 rounded-xl bg-white/5 border border-white/5 animate-pulse" />
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center">
          <p className="text-xs text-rose-400 mb-2">{error}</p>
          <button
            onClick={fetchForecast}
            className="text-xs text-rose-300 hover:text-rose-200 underline font-medium cursor-pointer"
          >
            Click here to retry
          </button>
        </div>
      )}

      {!isLoading && !error && data && (
        <div className="space-y-5">
          {/* Key Velocity Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            {/* Daily Burn Rate */}
            <div className="p-4 rounded-xl bg-background/50 border border-white/10 flex flex-col justify-between">
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                Current Burn Rate
              </span>
              <div className="mt-2">
                <p className="text-xl font-bold text-foreground">
                  ₹{data.velocity.daily_burn_rate.toLocaleString("en-IN")}{" "}
                  <span className="text-xs font-normal text-muted-foreground">/ day</span>
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Day {data.velocity.days_elapsed} of month ({data.velocity.days_remaining} days left)
                </p>
              </div>
            </div>

            {/* Safe Daily Spend */}
            <div className="p-4 rounded-xl bg-background/50 border border-white/10 flex flex-col justify-between">
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-emerald-400" />
                Safe Daily Spend
              </span>
              <div className="mt-2">
                <p className="text-xl font-bold text-emerald-400">
                  ₹{data.velocity.safe_daily_spend.toLocaleString("en-IN")}{" "}
                  <span className="text-xs font-normal text-muted-foreground">/ day</span>
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Allowance to finish month in budget
                </p>
              </div>
            </div>

            {/* Projected Month-End Total */}
            <div className="p-4 rounded-xl bg-background/50 border border-white/10 flex flex-col justify-between">
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                Projected Total
              </span>
              <div className="mt-2">
                <p className="text-xl font-bold text-foreground">
                  ₹{data.velocity.projected_month_end_spend.toLocaleString("en-IN")}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  {data.velocity.overall_budget_limit ? (
                    data.velocity.projected_overage > 0 ? (
                      <span className="text-rose-400 font-semibold">
                        +₹{data.velocity.projected_overage.toLocaleString("en-IN")} over limit
                      </span>
                    ) : (
                      <span className="text-emerald-400 font-semibold">Under budget limit</span>
                    )
                  ) : (
                    "No overall ceiling configured"
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Proactive Velocity Risk Alert Banner */}
          {(() => {
            const banner = getRiskBannerStyle(data.velocity.risk_level);
            return (
              <div className={`p-4 rounded-xl border flex items-center gap-3 ${banner.bg}`}>
                {banner.icon}
                <div className="flex-1">
                  <p className="text-xs font-semibold text-foreground">
                    Velocity Forecast:{" "}
                    <span className={`capitalize ${banner.text}`}>{data.velocity.risk_level}</span>
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
                    {data.velocity.risk_message}
                  </p>
                </div>
              </div>
            );
          })()}

          {/* Sub-Tabs: Velocity Forecast vs Smart Allocator */}
          <div className="flex items-center gap-2 border-b border-white/10 pb-2">
            <button
              onClick={() => setActiveTab("velocity")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === "velocity"
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Category Burn Velocity ({data.velocity.category_forecasts.length})
            </button>
            <button
              onClick={() => setActiveTab("allocator")}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === "allocator"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Smart Budget Allocator ({data.smart_allocations.length})
            </button>
          </div>

          {/* TAB 1: Category Velocity Breakdown */}
          {activeTab === "velocity" && (
            <div className="space-y-3">
              {data.velocity.category_forecasts.length === 0 ? (
                <div className="p-6 text-center rounded-xl bg-white/5 border border-white/5">
                  <p className="text-xs text-muted-foreground">
                    No category-wise budgets configured for this month. Use the Smart Budget Allocator tab to set limits with 1 click!
                  </p>
                </div>
              ) : (
                data.velocity.category_forecasts.map((cat) => {
                  const percent = Math.min(100, Math.round((cat.current_spent / cat.budget_limit) * 100));
                  const isOver = cat.risk_level === "critical";
                  return (
                    <div
                      key={cat.category_id}
                      className="p-3.5 rounded-xl bg-background/40 hover:bg-background/70 border border-white/10 transition-all flex flex-col gap-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-foreground">
                            {cat.category_name}
                          </span>
                          {cat.exhaustion_day ? (
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                                isOver
                                  ? "bg-rose-500/15 text-rose-400 border-rose-500/25"
                                  : "bg-amber-500/15 text-amber-400 border-amber-500/25"
                              }`}
                            >
                              Exhausts Day {cat.exhaustion_day}
                            </span>
                          ) : (
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                              On Track
                            </span>
                          )}
                        </div>

                        <div className="text-right">
                          <span className="text-xs font-semibold text-foreground">
                            ₹{cat.current_spent.toLocaleString("en-IN")}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {" "}
                            / ₹{cat.budget_limit.toLocaleString("en-IN")}
                          </span>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isOver
                              ? "bg-rose-500"
                              : percent > 80
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                          }`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-0.5">
                        <span>Burn: ₹{cat.daily_burn_rate.toLocaleString("en-IN")}/day</span>
                        <span>
                          Safe daily:{" "}
                          <strong className="text-foreground">
                            ₹{cat.safe_daily_spend.toLocaleString("en-IN")}/day
                          </strong>
                        </span>
                        <span>
                          Projected:{" "}
                          <strong className={isOver ? "text-rose-400" : "text-foreground"}>
                            ₹{cat.projected_month_end_spend.toLocaleString("en-IN")}
                          </strong>
                        </span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* TAB 2: Smart Dynamic Budget Allocator */}
          {activeTab === "allocator" && (
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground mb-1">
                AI analyzes your 60-day historical spending patterns and recommends realistic, optimal budget limits to prevent overspending without unrealistic restrictions.
              </p>

              {data.smart_allocations.length === 0 ? (
                <div className="p-6 text-center rounded-xl bg-white/5 border border-white/5">
                  <p className="text-xs text-muted-foreground">
                    Keep logging expenses for a few days to unlock tailored category budget recommendations.
                  </p>
                </div>
              ) : (
                data.smart_allocations.map((alloc) => {
                  const isApplying = applyingCategoryId === alloc.category_id;
                  const isSuccess = appliedCategorySuccess === alloc.category_id;
                  return (
                    <div
                      key={alloc.category_id}
                      className="p-4 rounded-xl bg-background/40 hover:bg-background/70 border border-white/10 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-xs font-bold text-foreground">
                            {alloc.category_name}
                          </h4>
                          <span className="text-[11px] text-muted-foreground">
                            (Avg: ₹{alloc.average_monthly_spend.toLocaleString("en-IN")}/mo)
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {alloc.reasoning}
                        </p>
                      </div>

                      <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
                        <div className="text-right">
                          <p className="text-[10px] text-muted-foreground uppercase font-medium">
                            Suggested Target
                          </p>
                          <p className="text-sm font-bold text-emerald-400">
                            ₹{alloc.suggested_budget.toLocaleString("en-IN")}
                          </p>
                        </div>

                        <button
                          onClick={() => handleApplyBudget(alloc.category_id, alloc.suggested_budget)}
                          disabled={isApplying}
                          className={`flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-xl transition-all cursor-pointer ${
                            isSuccess
                              ? "bg-emerald-500 text-zinc-950 shadow-md shadow-emerald-500/20"
                              : "bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40"
                          }`}
                        >
                          {isApplying ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              Applying...
                            </>
                          ) : isSuccess ? (
                            <>
                              <Check className="w-3.5 h-3.5" />
                              Applied!
                            </>
                          ) : (
                            <>
                              <Zap className="w-3.5 h-3.5" />
                              Apply Target
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
