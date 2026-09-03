"use client";

import React, { useState, useEffect } from "react";
import {
  Award,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  Target,
  ArrowUpRight,
  RefreshCw,
  Sparkles,
  PieChart,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { FinancialHealthScoreResponse } from "@/types/ai";

export default function FinancialHealthScoreCard() {
  const [data, setData] = useState<FinancialHealthScoreResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFullDigest, setShowFullDigest] = useState(false);

  const fetchScore = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<FinancialHealthScoreResponse>("/ai/health-score");
      setData(res.data);
    } catch (err: any) {
      setError(
        err?.response?.data?.error?.message ||
        err?.message ||
        "Could not compute financial health score."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchScore();
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 68) return "text-cyan-400";
    if (score >= 50) return "text-amber-400";
    return "text-rose-400";
  };

  const getScoreRingGradient = (score: number) => {
    if (score >= 80) return "from-emerald-500 to-teal-400";
    if (score >= 68) return "from-cyan-500 to-blue-500";
    if (score >= 50) return "from-amber-500 to-orange-400";
    return "from-rose-500 to-red-500";
  };

  return (
    <div className="relative overflow-hidden bg-card/60 backdrop-blur-xl border border-white/10 rounded-2xl p-5 sm:p-6 shadow-xl transition-all duration-300">
      {/* Glow */}
      <div className="absolute top-0 right-0 -mr-16 -mt-16 w-52 h-52 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -ml-16 -mb-16 w-52 h-52 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/20 via-teal-500/20 to-cyan-500/20 border border-emerald-500/30 text-emerald-400 shadow-md">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-foreground tracking-tight">
                Financial Health Score & Executive Summary
              </h2>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25">
                AI Wrapped
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Comprehensive 0–100 index based on adherence, savings velocity & discipline
            </p>
          </div>
        </div>

        <button
          onClick={fetchScore}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all disabled:opacity-50 cursor-pointer self-start sm:self-auto"
          title="Recalculate score"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-emerald-400" : ""}`} />
          <span>{isLoading ? "Analyzing..." : "Refresh Score"}</span>
        </button>
      </div>

      {isLoading && (
        <div className="space-y-4">
          <div className="h-28 rounded-xl bg-white/5 animate-pulse" />
          <div className="grid grid-cols-3 gap-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-xl bg-white/5 animate-pulse" />
            ))}
          </div>
        </div>
      )}

      {!isLoading && error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-center">
          <p className="text-xs text-rose-400 mb-2">{error}</p>
          <button
            onClick={fetchScore}
            className="text-xs text-rose-300 hover:text-rose-200 underline font-medium cursor-pointer"
          >
            Click here to retry
          </button>
        </div>
      )}

      {!isLoading && !error && data && (
        <div className="space-y-5">
          {/* Main Score Hero Card */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-white/[0.04] to-white/[0.01] border border-white/10 flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Score Ring / Badge */}
            <div className="flex items-center gap-4">
              <div className="relative flex items-center justify-center w-24 h-24 rounded-2xl bg-background/90 border border-white/15 shadow-inner">
                <div className="text-center">
                  <span className={`text-3xl font-extrabold tracking-tight ${getScoreColor(data.health_score)}`}>
                    {data.health_score}
                  </span>
                  <span className="text-[11px] text-muted-foreground block -mt-1">/ 100</span>
                </div>
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <span className={`text-2xl font-extrabold ${getScoreColor(data.health_score)}`}>
                    {data.letter_grade}
                  </span>
                  <span className="text-sm font-semibold text-foreground">
                    • {data.status_label}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Evaluated for <strong>{data.period_month}</strong>
                </p>
                <div className="mt-2 flex items-center gap-2 text-[11px] text-cyan-300">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Top category: <strong>{data.top_spend_category}</strong></span>
                </div>
              </div>
            </div>

            {/* Three Pillar Breakdown Bars */}
            <div className="w-full md:w-1/2 space-y-3">
              {/* Pillar 1 */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground font-medium">Budget Adherence</span>
                  <span className="font-bold text-foreground">
                    {data.pillars.budget_adherence} <span className="text-muted-foreground font-normal">/ 40 pts</span>
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-400 transition-all duration-500"
                    style={{ width: `${(data.pillars.budget_adherence / 40) * 100}%` }}
                  />
                </div>
              </div>

              {/* Pillar 2 */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground font-medium">Savings Velocity & Burn</span>
                  <span className="font-bold text-foreground">
                    {data.pillars.savings_velocity} <span className="text-muted-foreground font-normal">/ 35 pts</span>
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                    style={{ width: `${(data.pillars.savings_velocity / 35) * 100}%` }}
                  />
                </div>
              </div>

              {/* Pillar 3 */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground font-medium">Category Discipline</span>
                  <span className="font-bold text-foreground">
                    {data.pillars.category_discipline} <span className="text-muted-foreground font-normal">/ 25 pts</span>
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-purple-400 transition-all duration-500"
                    style={{ width: `${(data.pillars.category_discipline / 25) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Executive Summary Paragraph */}
          <div className="p-4 rounded-xl bg-background/50 border border-white/10">
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              Executive AI Digest
            </h4>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {data.executive_summary}
            </p>
          </div>

          {/* Toggle Full Digest Details */}
          <div>
            <button
              onClick={() => setShowFullDigest(!showFullDigest)}
              className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer"
            >
              <span>{showFullDigest ? "Hide Achievements & Goals" : "View Achievements & Strategic Goals"}</span>
              {showFullDigest ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showFullDigest && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 animate-in fade-in duration-200">
                {/* Achievements */}
                <div className="p-4 rounded-xl bg-background/40 border border-white/10 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    Key Financial Milestones
                  </h4>
                  <ul className="space-y-1.5">
                    {data.key_achievements.map((ach, idx) => (
                      <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                        <span className="text-emerald-400 text-xs">✓</span>
                        <span>{ach}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Goals */}
                <div className="p-4 rounded-xl bg-background/40 border border-white/10 space-y-2">
                  <h4 className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                    <Target className="w-4 h-4" />
                    Strategic Goals for Next Month
                  </h4>
                  <ul className="space-y-1.5">
                    {data.improvement_goals.map((goal, idx) => (
                      <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                        <ArrowUpRight className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                        <span>{goal}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
