"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  RefreshCw,
  Zap,
  AlertTriangle,
  Repeat,
  Flame,
  ArrowRight,
  TrendingDown,
  Info,
  CheckCircle,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { SpendingInsight, SpendingInsightsResponse, InsightCategory } from "@/types/ai";

export default function SmartInsightsCard() {
  const [data, setData] = useState<SpendingInsightsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | InsightCategory>("all");

  const fetchInsights = async (force: boolean = false) => {
    if (force) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      if (force) {
        const res = await apiClient.post<SpendingInsightsResponse>("/ai/insights/refresh");
        setData(res.data);
      } else {
        const res = await apiClient.get<SpendingInsightsResponse>("/ai/insights");
        setData(res.data);
      }
    } catch (err: any) {
      setError(
        err?.message ||
        err?.response?.data?.error?.message ||
        "Could not load AI insights right now."
      );
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchInsights(false);
  }, []);

  const filteredInsights = data?.insights.filter((item) => {
    if (activeTab === "all") return true;
    return item.type === activeTab;
  }) || [];

  const getBadgeConfig = (type: InsightCategory) => {
    switch (type) {
      case "quick_win":
        return {
          label: "Quick Win",
          icon: <Zap className="w-3.5 h-3.5" />,
          colorClass: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        };
      case "budget_alert":
        return {
          label: "Budget Alert",
          icon: <AlertTriangle className="w-3.5 h-3.5" />,
          colorClass: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        };
      case "subscription":
        return {
          label: "Subscription",
          icon: <Repeat className="w-3.5 h-3.5" />,
          colorClass: "bg-violet-500/10 text-violet-400 border-violet-500/20",
        };
      case "high_impact":
        return {
          label: "High Impact",
          icon: <Flame className="w-3.5 h-3.5" />,
          colorClass: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
        };
      default:
        return {
          label: "Insight",
          icon: <Info className="w-3.5 h-3.5" />,
          colorClass: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
        };
    }
  };

  return (
    <div className="relative overflow-hidden bg-card/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl transition-all duration-300">
      {/* Background Decorative Glow */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-56 h-56 rounded-full bg-emerald-500/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-56 h-56 rounded-full bg-cyan-500/5 blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/20 via-cyan-500/20 to-violet-500/20 border border-emerald-500/30 text-emerald-400 shadow-md shadow-emerald-500/10">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-foreground tracking-tight">
                AI Spending Insights & Advisor
              </h2>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                AI Powered
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Personalized cost-saving advice generated from your recent expenses
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {data?.provider && (
            <span className="text-[11px] text-muted-foreground hidden md:inline-block px-2.5 py-1 rounded-lg bg-white/5 border border-white/5">
              Engine: <span className="text-foreground font-medium">{data.provider}</span>
            </span>
          )}
          <button
            onClick={() => fetchInsights(true)}
            disabled={isRefreshing || isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all disabled:opacity-50 cursor-pointer"
            title="Refresh AI Analysis"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-emerald-400" : ""}`} />
            <span>{isRefreshing ? "Analyzing..." : "Refresh"}</span>
          </button>
        </div>
      </div>

      {/* Potential Monthly Savings Highlight Banner */}
      {data && data.total_potential_monthly_savings > 0 && (
        <div className="mb-5 p-4 rounded-xl bg-gradient-to-r from-emerald-950/40 via-emerald-900/20 to-card border border-emerald-500/30 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
              <TrendingDown className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-emerald-300 font-medium">
                Identified Potential Monthly Savings
              </p>
              <p className="text-lg font-bold text-foreground">
                ~₹{data.total_potential_monthly_savings.toLocaleString("en-IN")}{" "}
                <span className="text-xs font-normal text-muted-foreground">/ month</span>
              </p>
            </div>
          </div>
          <div className="hidden sm:block text-right">
            <span className="text-xs text-muted-foreground">
              Based on {data.insights.length} personalized recommendations
            </span>
          </div>
        </div>
      )}

      {/* Category Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-4 scrollbar-none">
        {(
          [
            { id: "all", label: "All Insights" },
            { id: "quick_win", label: "Quick Wins" },
            { id: "budget_alert", label: "Budget Alerts" },
            { id: "subscription", label: "Subscriptions" },
            { id: "high_impact", label: "High Impact" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg whitespace-nowrap transition-all cursor-pointer ${
              activeTab === tab.id
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm"
                : "text-muted-foreground hover:text-foreground bg-white/5 hover:bg-white/10 border border-transparent"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="p-4 rounded-xl border border-white/5 bg-white/5 animate-pulse flex flex-col gap-2"
            >
              <div className="flex items-center justify-between">
                <div className="h-4 w-28 bg-white/10 rounded" />
                <div className="h-4 w-16 bg-white/10 rounded" />
              </div>
              <div className="h-3 w-3/4 bg-white/5 rounded mt-1" />
              <div className="h-8 w-full bg-white/5 rounded mt-2" />
            </div>
          ))}
        </div>
      )}

      {/* Error Message */}
      {!isLoading && error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center">
          <p className="text-xs text-rose-400 mb-2">{error}</p>
          <button
            onClick={() => fetchInsights(true)}
            className="text-xs text-rose-300 hover:text-rose-200 underline font-medium cursor-pointer"
          >
            Click here to retry
          </button>
        </div>
      )}

      {/* Insights List */}
      {!isLoading && !error && (
        <div className="space-y-3">
          {filteredInsights.length === 0 ? (
            <div className="p-6 text-center rounded-xl bg-white/5 border border-white/5">
              <CheckCircle className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-50" />
              <p className="text-sm font-medium text-foreground">No insights in this category</p>
              <p className="text-xs text-muted-foreground mt-1">
                Your spending in this area looks healthy and well-managed!
              </p>
            </div>
          ) : (
            filteredInsights.map((insight) => {
              const badge = getBadgeConfig(insight.type);
              return (
                <div
                  key={insight.id}
                  className="p-4 rounded-xl bg-background/50 hover:bg-background/80 border border-white/10 hover:border-white/20 transition-all group flex flex-col gap-2.5 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md border ${badge.colorClass}`}
                      >
                        {badge.icon}
                        {badge.label}
                      </span>
                      <h3 className="text-sm font-semibold text-foreground group-hover:text-emerald-400 transition-colors">
                        {insight.title}
                      </h3>
                    </div>

                    {insight.potential_savings && (
                      <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md whitespace-nowrap">
                        Save ~₹{insight.potential_savings.toLocaleString("en-IN")}/mo
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {insight.description}
                  </p>

                  {insight.action_tip && (
                    <div className="mt-1 p-2.5 rounded-lg bg-white/5 border border-white/5 flex items-start gap-2 text-xs text-foreground/90">
                      <ArrowRight className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>
                        <strong className="text-emerald-400 font-medium">Recommended Action:</strong>{" "}
                        {insight.action_tip}
                      </span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
