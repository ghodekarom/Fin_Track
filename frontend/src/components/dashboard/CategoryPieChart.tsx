"use client";

import React from "react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import { CategoryBreakdown } from "../../lib/queries/dashboard";
import { formatCurrency } from "../../lib/utils/currency";
import { EmptyState } from "../ui/EmptyState";
import { PieChartIcon } from "lucide-react";

interface CategoryPieChartProps {
  data?: CategoryBreakdown[];
}

// Curated slate-emerald theme colors
const COLORS = [
  "#10b981", // Emerald
  "#3b82f6", // Blue
  "#8b5cf6", // Purple
  "#ec4899", // Pink
  "#f59e0b", // Amber
  "#06b6d4", // Cyan
  "#14b8a6", // Teal
  "#f43f5e", // Rose
];

export function CategoryPieChart({ data = [] }: CategoryPieChartProps) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No Category Data Available"
        description="Add expenses with categories to render the breakdown donut chart."
        icon={<PieChartIcon className="h-10 w-10 text-muted-foreground/60" />}
      />
    );
  }

  const chartData = data.map((item) => ({
    name: item.category_name,
    value: Number(item.total_spent),
    percentage: item.percentage,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-zinc-950/90 border border-white/10 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <p className="text-xs font-semibold text-white">{data.name}</p>
          <div className="flex items-center gap-4 mt-1">
            <span className="text-xs font-bold text-primary">{formatCurrency(data.value)}</span>
            <span className="text-[10px] text-muted-foreground bg-white/5 px-1.5 py-0.5 rounded font-mono">
              {data.percentage.toFixed(1)}%
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 h-[340px] flex flex-col justify-between">
      <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-2">
        Spending Breakdown by Category
      </h2>
      <div className="flex-1 min-h-0 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={85}
              paddingAngle={3}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                  stroke="rgba(0,0,0,0.2)"
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              iconSize={8}
              iconType="circle"
              wrapperStyle={{ fontSize: "11px", paddingTop: "15px" }}
              formatter={(value, entry: any) => {
                const percent = entry.payload?.percentage ?? 0;
                return <span className="text-neutral-300 font-semibold">{value} ({percent.toFixed(0)}%)</span>;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
export default CategoryPieChart;
