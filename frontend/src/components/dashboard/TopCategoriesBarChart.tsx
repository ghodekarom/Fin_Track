"use client";

import React from "react";
import { ResponsiveContainer, BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { TopCategory } from "../../lib/queries/dashboard";
import { formatCurrency } from "../../lib/utils/currency";
import { EmptyState } from "../ui/EmptyState";
import { Trophy } from "lucide-react";

interface TopCategoriesBarChartProps {
  data?: TopCategory[];
}

const COLORS = [
  "#3b82f6", // Blue
  "#10b981", // Emerald
  "#8b5cf6", // Purple
  "#f59e0b", // Amber
  "#ec4899", // Pink
];

export function TopCategoriesBarChart({ data = [] }: TopCategoriesBarChartProps) {
  if (data.length === 0) {
    return (
      <EmptyState
        title="No Ranking Data"
        description="Log expenses to see your top category ranks."
        icon={<Trophy className="h-10 w-10 text-muted-foreground/60" />}
      />
    );
  }

  const chartData = data.map((item) => ({
    name: item.category_name,
    value: Number(item.total_spent),
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const entry = payload[0];
      return (
        <div className="bg-zinc-950/90 border border-white/10 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <p className="text-xs font-semibold text-white">{entry.payload.name}</p>
          <p className="text-sm font-bold text-primary mt-1">{formatCurrency(entry.value)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass-card p-6 rounded-2xl border border-white/5 h-[340px] flex flex-col justify-between">
      <div className="flex items-center justify-between border-b border-white/5 pb-2.5 mb-2">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
          <Trophy className="h-4 w-4 text-amber-400" />
          Top Category Spend Ranking
        </h2>
      </div>
      <div className="flex-1 min-h-0 relative">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 15, right: 10, left: -20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="#6b7280"
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#6b7280"
              fontSize={10}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="value"
              radius={[4, 4, 0, 0]}
              barSize={28}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default TopCategoriesBarChart;
