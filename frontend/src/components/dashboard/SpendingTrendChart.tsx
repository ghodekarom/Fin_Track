"use client";

import React, { useState } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { SpendingTrend } from "../../lib/queries/dashboard";
import { formatCurrency } from "../../lib/utils/currency";
import { EmptyState } from "../ui/EmptyState";
import { TrendingUp, BarChart2 } from "lucide-react";
import { format, parseISO } from "date-fns";

interface SpendingTrendChartProps {
  data?: SpendingTrend[];
  interval: "daily" | "weekly" | "monthly";
  onIntervalChange: (interval: "daily" | "weekly" | "monthly") => void;
}

export function SpendingTrendChart({
  data = [],
  interval,
  onIntervalChange,
}: SpendingTrendChartProps) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No Trend Data Available"
        description="Log transactions to view spending patterns over days, weeks, or months."
        icon={<BarChart2 className="h-10 w-10 text-muted-foreground/60" />}
      />
    );
  }

  const chartData = data.map((item) => ({
    rawDate: item.date,
    dateDisplay: item.date
      ? interval === "daily"
        ? format(parseISO(item.date), "dd MMM")
        : interval === "weekly"
        ? `Wk ${format(parseISO(item.date), "ww")}`
        : format(parseISO(item.date), "MMM yyyy")
      : "Unknown",
    Amount: Number(item.total_spent),
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const entry = payload[0];
      return (
        <div className="bg-zinc-950/90 border border-white/10 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
            {interval === "daily" ? "Daily Total" : interval === "weekly" ? "Weekly Total" : "Monthly Total"}
          </p>
          <p className="text-xs font-semibold text-white mt-0.5">{entry.payload.dateDisplay}</p>
          <p className="text-sm font-bold text-primary mt-1.5">{formatCurrency(entry.value)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 h-[340px] flex flex-col justify-between">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          Spending Pattern Over Time
        </h2>

        {/* Interval Select Controls */}
        <div className="flex items-center gap-1.5 bg-white/5 border border-white/5 p-1 rounded-xl shrink-0 self-start sm:self-auto">
          {(["daily", "weekly", "monthly"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => onIntervalChange(mode)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg capitalize transition ${
                interval === mode
                  ? "bg-primary text-black"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-0 relative mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
            <XAxis
              dataKey="dateDisplay"
              stroke="#6b7280"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis
              stroke="#6b7280"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              dx={-5}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="Amount"
              stroke="#10b981"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorAmount)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
export default SpendingTrendChart;
