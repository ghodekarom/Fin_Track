"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { ExpenseForm } from "@/components/expenses/ExpenseForm";
import { ArrowLeft, Plus } from "lucide-react";

export default function NewExpense() {
  const router = useRouter();

  const handleSuccess = () => {
    router.push("/expenses");
  };

  const handleCancel = () => {
    router.push("/expenses");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in pb-12">
      {/* Back button link */}
      <button
        onClick={handleCancel}
        className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground hover:text-white transition"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Ledger
      </button>

      {/* Form Card wrapper */}
      <div className="glass-card p-6 md:p-8 rounded-3xl border border-white/5 space-y-6">
        <div className="flex items-center gap-3 border-b border-white/5 pb-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 text-primary border border-primary/20">
            <Plus className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Log New Expense</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Fill in the details below to add a transaction record.
            </p>
          </div>
        </div>

        <ExpenseForm onSuccess={handleSuccess} onCancel={handleCancel} />
      </div>
    </div>
  );
}
