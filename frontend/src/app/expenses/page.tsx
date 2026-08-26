"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useExpenses, ExpenseFilters as FiltersType } from "@/lib/queries/expenses";
import { ExpenseFilters } from "@/components/expenses/ExpenseFilters";
import { ExpenseList } from "@/components/expenses/ExpenseList";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Plus, Receipt } from "lucide-react";

export default function Expenses() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<FiltersType>({
    sort_by: "date",
    sort_order: "desc",
  });

  const PAGE_SIZE = 15;

  const { data, isLoading, isError, refetch } = useExpenses(filters, page, PAGE_SIZE);

  const handleFilterChange = (newFilters: FiltersType) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
  };

  const handleResetFilters = () => {
    setFilters({
      sort_by: "date",
      sort_order: "desc",
    });
    setPage(1);
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Receipt className="h-6 w-6 text-primary" />
            Expenses Ledger
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Browse, search, sort, and filter your historical transactions.
          </p>
        </div>
        <Link
          href="/expenses/new"
          className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-black bg-primary hover:bg-primary/90 rounded-xl transition duration-150 active:scale-95 shrink-0 self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          Log New Expense
        </Link>
      </div>

      {/* Filter controls */}
      <ExpenseFilters
        filters={filters}
        onChange={handleFilterChange}
        onReset={handleResetFilters}
      />

      {/* Data listing */}
      {isError ? (
        <ErrorState onRetry={refetch} />
      ) : (
        <ExpenseList
          expenses={data?.items || []}
          currentPage={page}
          totalPages={data?.pages || 1}
          onPageChange={setPage}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
