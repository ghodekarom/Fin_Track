"use client";

import React, { useState } from "react";
import { useCategories } from "../../lib/queries/categories";
import { ExpenseFilters as FiltersType } from "../../lib/queries/expenses";
import { Search, SlidersHorizontal, RotateCcw, Calendar, ChevronDown, ChevronUp } from "lucide-react";
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth } from "date-fns";

interface ExpenseFiltersProps {
  filters: FiltersType;
  onChange: (updatedFilters: FiltersType) => void;
  onReset: () => void;
}

export function ExpenseFilters({ filters, onChange, onReset }: ExpenseFiltersProps) {
  const { data: categories } = useCategories();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [quickDateRange, setQuickDateRange] = useState("all");

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, search: e.target.value });
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, category_id: e.target.value || undefined });
  };

  const handlePaymentModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, payment_mode: (e.target.value || undefined) as any });
  };

  const handleSortByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, sort_by: e.target.value as any });
  };

  const handleSortOrderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({ ...filters, sort_order: e.target.value as any });
  };

  const handleAmountMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value === "" ? undefined : parseFloat(e.target.value);
    onChange({ ...filters, amount_min: val });
  };

  const handleAmountMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value === "" ? undefined : parseFloat(e.target.value);
    onChange({ ...filters, amount_max: val });
  };

  const handleCustomDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, date_from: e.target.value || undefined });
  };

  const handleCustomDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, date_to: e.target.value || undefined });
  };

  // Quick Date Select handler
  const handleQuickDateSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setQuickDateRange(val);

    const today = new Date();
    let fromDateStr: string | undefined = undefined;
    let toDateStr: string | undefined = undefined;

    if (val === "week") {
      fromDateStr = format(startOfWeek(today, { weekStartsOn: 1 }), "yyyy-MM-dd");
      toDateStr = format(endOfWeek(today, { weekStartsOn: 1 }), "yyyy-MM-dd");
    } else if (val === "month") {
      fromDateStr = format(startOfMonth(today), "yyyy-MM-dd");
      toDateStr = format(endOfMonth(today), "yyyy-MM-dd");
    }

    onChange({
      ...filters,
      date_from: fromDateStr,
      date_to: toDateStr,
    });
  };

  const toggleAdvanced = () => setShowAdvanced(!showAdvanced);

  return (
    <div className="glass-card p-5 rounded-2xl border border-white/5 space-y-4">
      {/* Primary search bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3 h-4.5 w-4.5 text-muted-foreground" />
          <input
            type="text"
            value={filters.search || ""}
            onChange={handleSearchChange}
            placeholder="Search by title or notes..."
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-muted-foreground focus:outline-none focus:border-primary transition"
          />
        </div>

        <div className="flex gap-2">
          {/* Advanced toggle button */}
          <button
            onClick={toggleAdvanced}
            className={`flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl border transition ${
              showAdvanced || filters.category_id || filters.payment_mode || filters.amount_min || filters.amount_max || filters.date_from
                ? "bg-primary/10 border-primary text-primary"
                : "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10 hover:text-white"
            }`}
          >
            <SlidersHorizontal className="h-4 w-4" />
            <span>Filters</span>
            {showAdvanced ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>

          {/* Reset Filters button */}
          <button
            onClick={() => {
              setQuickDateRange("all");
              onReset();
            }}
            className="flex items-center justify-center p-2.5 text-sm font-medium bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white border border-white/10 rounded-xl transition"
            title="Reset Filters"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Advanced filters area */}
      {showAdvanced && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 pt-4 border-t border-white/5 animate-fade-in">
          {/* Category Filter */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Category</label>
            <select
              value={filters.category_id || ""}
              onChange={handleCategoryChange}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            >
              <option value="" className="bg-zinc-900">All Categories</option>
              {categories?.map((cat) => (
                <option key={cat.id} value={cat.id} className="bg-zinc-900">
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          {/* Payment Mode */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Payment Mode</label>
            <select
              value={filters.payment_mode || ""}
              onChange={handlePaymentModeChange}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            >
              <option value="" className="bg-zinc-900">All Payment Modes</option>
              <option value="cash" className="bg-zinc-900">Cash</option>
              <option value="card" className="bg-zinc-900">Card</option>
              <option value="upi" className="bg-zinc-900">UPI</option>
              <option value="other" className="bg-zinc-900">Other</option>
            </select>
          </div>

          {/* Quick Date Range */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Date Range</label>
            <select
              value={quickDateRange}
              onChange={handleQuickDateSelect}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            >
              <option value="all" className="bg-zinc-900">All Time</option>
              <option value="week" className="bg-zinc-900">This Week</option>
              <option value="month" className="bg-zinc-900">This Month</option>
              <option value="custom" className="bg-zinc-900">Custom Dates...</option>
            </select>
          </div>

          {/* Sort Field */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Sort By</label>
            <select
              value={filters.sort_by || "date"}
              onChange={handleSortByChange}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            >
              <option value="date" className="bg-zinc-900">Date</option>
              <option value="amount" className="bg-zinc-900">Amount</option>
              <option value="category" className="bg-zinc-900">Category</option>
            </select>
          </div>

          {/* Sort Direction */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Direction</label>
            <select
              value={filters.sort_order || "desc"}
              onChange={handleSortOrderChange}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            >
              <option value="desc" className="bg-zinc-900">Descending</option>
              <option value="asc" className="bg-zinc-900">Ascending</option>
            </select>
          </div>

          {/* Custom Date Ranges */}
          {quickDateRange === "custom" && (
            <>
              <div className="space-y-1.5">
                <label className="text-xs text-muted-foreground font-medium">Date From</label>
                <input
                  type="date"
                  value={filters.date_from || ""}
                  onChange={handleCustomDateFromChange}
                  className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-muted-foreground font-medium">Date To</label>
                <input
                  type="date"
                  value={filters.date_to || ""}
                  onChange={handleCustomDateToChange}
                  className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
                />
              </div>
            </>
          )}

          {/* Amount Brackets */}
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Min Amount (₹)</label>
            <input
              type="number"
              placeholder="0"
              value={filters.amount_min === undefined ? "" : filters.amount_min}
              onChange={handleAmountMinChange}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground font-medium">Max Amount (₹)</label>
            <input
              type="number"
              placeholder="Any"
              value={filters.amount_max === undefined ? "" : filters.amount_max}
              onChange={handleAmountMaxChange}
              className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-3 py-2 text-sm text-white focus:outline-none transition"
            />
          </div>
        </div>
      )}
    </div>
  );
}
export default ExpenseFilters;
