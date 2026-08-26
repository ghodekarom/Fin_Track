"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { budgetSchema, BudgetFormValues } from "../../lib/validators/budget";
import { useCategories } from "../../lib/queries/categories";
import { useCreateBudget } from "../../lib/queries/budgets";
import { Landmark, AlertCircle } from "lucide-react";

interface BudgetFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
  defaultMonth?: string; // YYYY-MM
}

export function BudgetForm({ onSuccess, onCancel, defaultMonth }: BudgetFormProps) {
  const { data: categories } = useCategories();
  const createBudgetMutation = useCreateBudget();

  // Get current month format YYYY-MM
  const getCurrentMonthStr = () => {
    const d = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    return `${d.getFullYear()}-${mm}`;
  };

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    setError,
  } = useForm<BudgetFormValues>({
    resolver: zodResolver(budgetSchema),
    defaultValues: {
      scope: "overall",
      category_id: "",
      period_month: defaultMonth || getCurrentMonthStr(),
      limit_amount: 0,
    },
  });

  const selectedScope = watch("scope");

  const onSubmit = async (values: BudgetFormValues) => {
    try {
      // Backend expects period_month to be YYYY-MM-DD
      const dateString = `${values.period_month}-01`;
      
      const payload = {
        scope: values.scope,
        category_id: values.scope === "category" ? values.category_id || null : null,
        period_month: dateString,
        limit_amount: Number(values.limit_amount),
      };

      await createBudgetMutation.mutateAsync(payload);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      // Map API details back to form fields
      const detail = err.message || "Failed to set budget limit.";
      setError("root", { type: "server", message: detail });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3 pb-3 border-b border-white/5">
        <Landmark className="h-5 w-5 text-primary" />
        <h2 className="text-md font-semibold text-white">Set Budget Target</h2>
      </div>

      {errors.root && (
        <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/10 border border-destructive/20 p-3.5 rounded-xl">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errors.root.message}</span>
        </div>
      )}

      {/* Scope selector */}
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground font-medium">Budget Scope</label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setValue("scope", "overall")}
            className={`py-2.5 text-xs font-semibold rounded-xl border transition ${
              selectedScope === "overall"
                ? "bg-primary text-black border-primary"
                : "bg-white/5 text-muted-foreground border-white/10 hover:bg-white/10"
            }`}
          >
            Overall Monthly Limit
          </button>
          <button
            type="button"
            onClick={() => setValue("scope", "category")}
            className={`py-2.5 text-xs font-semibold rounded-xl border transition ${
              selectedScope === "category"
                ? "bg-primary text-black border-primary"
                : "bg-white/5 text-muted-foreground border-white/10 hover:bg-white/10"
            }`}
          >
            Category-Specific Limit
          </button>
        </div>
      </div>

      {/* Category selection */}
      {selectedScope === "category" && (
        <div className="space-y-1.5 animate-fade-in">
          <label className="text-xs text-muted-foreground font-medium">Select Category</label>
          <select
            {...register("category_id")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          >
            <option value="" className="bg-zinc-900">-- Choose Category --</option>
            {categories?.map((category) => (
              <option key={category.id} value={category.id} className="bg-zinc-900">
                {category.name}
              </option>
            ))}
          </select>
          {errors.category_id && (
            <p className="text-xs text-destructive mt-1">{errors.category_id.message}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {/* Month selector */}
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Target Month</label>
          <input
            type="month"
            {...register("period_month")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          />
          {errors.period_month && (
            <p className="text-xs text-destructive mt-1">{errors.period_month.message}</p>
          )}
        </div>

        {/* Limit Amount */}
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Limit Amount (₹)</label>
          <input
            type="number"
            step="0.01"
            placeholder="e.g. 15000"
            {...register("limit_amount")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          />
          {errors.limit_amount && (
            <p className="text-xs text-destructive mt-1">{errors.limit_amount.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-white/5">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2.5 text-xs text-muted-foreground hover:text-white"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={createBudgetMutation.isPending}
          className="px-5 py-2.5 text-xs font-semibold bg-primary text-black rounded-xl hover:bg-primary/90 transition active:scale-95 disabled:opacity-50"
        >
          Save Budget Limit
        </button>
      </div>
    </form>
  );
}
export default BudgetForm;
