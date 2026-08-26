"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Expense } from "../../types/expense";
import { formatCurrency } from "../../lib/utils/currency";
import { format } from "date-fns";
import { Edit2, Trash2, ChevronLeft, ChevronRight, CreditCard, Landmark, Wallet, CircleEllipsis } from "lucide-react";
import { useDeleteExpense } from "../../lib/queries/expenses";
import { DeleteConfirmDialog } from "./DeleteConfirmDialog";

interface ExpenseListProps {
  expenses: Expense[];
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
}

export function ExpenseList({
  expenses,
  currentPage,
  totalPages,
  onPageChange,
  isLoading = false,
}: ExpenseListProps) {
  const deleteMutation = useDeleteExpense();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDeleteClick = (id: string) => {
    setDeletingId(id);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingId) return;
    try {
      await deleteMutation.mutateAsync(deletingId);
      setDeletingId(null);
    } catch (err) {
      console.error(err);
    }
  };

  const getPaymentModeIcon = (mode: string | null) => {
    switch (mode) {
      case "cash":
        return <Wallet className="h-3 w-3 mr-1 text-emerald-400" />;
      case "card":
        return <CreditCard className="h-3 w-3 mr-1 text-purple-400" />;
      case "upi":
        return <Landmark className="h-3 w-3 mr-1 text-teal-400" />;
      default:
        return <CircleEllipsis className="h-3 w-3 mr-1 text-neutral-400" />;
    }
  };

  const getPaymentModeBadge = (mode: string | null) => {
    if (!mode) return <span className="text-neutral-500">—</span>;
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/5 border border-white/5 text-neutral-300 capitalize">
        {getPaymentModeIcon(mode)}
        {mode}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Table Card wrapper */}
      <div className="glass-card rounded-2xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 text-xs font-semibold uppercase tracking-wider text-muted-foreground bg-white/2">
                <th className="px-6 py-4">Title</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Category</th>
                <th className="px-6 py-4">Payment</th>
                <th className="px-6 py-4 text-right">Amount</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm text-neutral-200">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, idx) => (
                  <tr key={idx} className="animate-pulse">
                    <td className="px-6 py-4"><div className="h-4 bg-white/5 rounded w-32" /></td>
                    <td className="px-6 py-4"><div className="h-4 bg-white/5 rounded w-20" /></td>
                    <td className="px-6 py-4"><div className="h-4 bg-white/5 rounded w-24" /></td>
                    <td className="px-6 py-4"><div className="h-4 bg-white/5 rounded w-16" /></td>
                    <td className="px-6 py-4 text-right"><div className="h-4 bg-white/5 rounded w-16 ml-auto" /></td>
                    <td className="px-6 py-4 text-right"><div className="h-6 bg-white/5 rounded w-12 ml-auto" /></td>
                  </tr>
                ))
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground text-sm">
                    No matching expense records found.
                  </td>
                </tr>
              ) : (
                expenses.map((expense) => (
                  <tr key={expense.id} className="hover:bg-white/2 transition duration-150">
                    <td className="px-6 py-4 font-medium text-white max-w-[200px] truncate">
                      <div>
                        <div className="font-semibold">{expense.title}</div>
                        {expense.notes && (
                          <div className="text-xs text-muted-foreground font-normal truncate mt-0.5" title={expense.notes}>
                            {expense.notes}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-muted-foreground text-xs">
                      {format(new Date(expense.expense_date), "dd MMM yyyy")}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold bg-primary/10 text-primary border border-primary/15">
                        {expense.category.name}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getPaymentModeBadge(expense.payment_mode)}
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap font-bold text-white">
                      {formatCurrency(expense.amount)}
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/expenses/${expense.id}/edit`}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white transition"
                          title="Edit expense"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </Link>
                        <button
                          onClick={() => handleDeleteClick(expense.id)}
                          className="p-1.5 rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive transition"
                          title="Delete expense"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination component controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2 pt-2 text-xs text-muted-foreground">
          <div>
            Showing page <span className="font-medium text-white">{currentPage}</span> of{" "}
            <span className="font-medium text-white">{totalPages}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1 || isLoading}
              className="flex items-center gap-1 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-40 transition border border-white/5 text-white"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Previous</span>
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages || isLoading}
              className="flex items-center gap-1 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 disabled:opacity-40 transition border border-white/5 text-white"
            >
              <span>Next</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Confirmation modal */}
      <DeleteConfirmDialog
        isOpen={!!deletingId}
        isDeleting={deleteMutation.isPending}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeletingId(null)}
      />
    </div>
  );
}
export default ExpenseList;
