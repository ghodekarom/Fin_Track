"use client";

import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import { PaymentModeBreakdown } from "../../lib/queries/dashboard";
import { formatCurrency } from "../../lib/utils/currency";
import { EmptyState } from "../ui/EmptyState";
import { CreditCard } from "lucide-react";

interface PaymentModeChartProps {
  data?: PaymentModeBreakdown[];
}

const COLORS: Record<string, string> = {
  card: "#3b82f6",  // Blue
  upi: "#10b981",   // Emerald
  cash: "#f59e0b",  // Amber
  other: "#8b5cf6", // Purple
};

export function PaymentModeChart({ data = [] }: PaymentModeChartProps) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No Payment Mode Data"
        description="Add expenses with payment modes to render the breakdown."
        icon={<CreditCard className="h-10 w-10 text-muted-foreground/60" />}
      />
    );
  }

  const chartData = data.map((item) => ({
    name: item.payment_mode.toUpperCase(),
    value: Number(item.total_spent),
    percentage: item.percentage,
    rawMode: item.payment_mode,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const entry = payload[0].payload;
      return (
        <div className="bg-zinc-950/90 border border-white/10 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <p className="text-xs font-semibold text-white">{entry.name}</p>
          <div className="flex items-center gap-4 mt-1">
            <span className="text-xs font-bold text-primary">{formatCurrency(entry.value)}</span>
            <span className="text-[10px] text-muted-foreground bg-white/5 px-1.5 py-0.5 rounded font-mono">
              {entry.percentage.toFixed(1)}%
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 h-[340px] flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-white/5 pb-2.5 mb-2">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-primary" />
          Spending by Payment Mode
        </h2>
      </div>
      <div className="flex-1 min-h-0 relative flex items-center justify-center">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<CustomTooltip />} />
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={62}
              outerRadius={82}
              paddingAngle={4}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[entry.rawMode] || "#6b7280"}
                />
              ))}
            </Pie>
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value) => (
                <span className="text-xs text-neutral-300 font-semibold uppercase tracking-wider pl-1">
                  {value}
                </span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default PaymentModeChart;
