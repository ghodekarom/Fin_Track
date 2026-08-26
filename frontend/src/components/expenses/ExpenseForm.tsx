"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { expenseSchema, ExpenseFormValues } from "../../lib/validators/expense";
import { useCategories, useCreateCategory } from "../../lib/queries/categories";
import { useCreateExpense, useUpdateExpense } from "../../lib/queries/expenses";
import { Expense } from "../../types/expense";
import { Plus, Tag, HelpCircle, AlertCircle, Calendar } from "lucide-react";

interface ExpenseFormProps {
  initialData?: Expense;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function ExpenseForm({ initialData, onSuccess, onCancel }: ExpenseFormProps) {
  const { data: categories } = useCategories();
  const createCategoryMutation = useCreateCategory();
  const createExpenseMutation = useCreateExpense();
  const updateExpenseMutation = useUpdateExpense();

  const [isNewCategoryActive, setIsNewCategoryActive] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [inlineCategoryError, setInlineCategoryError] = useState("");

  const isEditMode = !!initialData;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
    setError,
  } = useForm<ExpenseFormValues>({
    resolver: zodResolver(expenseSchema),
    defaultValues: {
      title: initialData?.title || "",
      category_id: initialData?.category_id || "",
      amount: initialData?.amount || 0,
      expense_date: initialData?.expense_date || new Date().toISOString().split("T")[0],
      notes: initialData?.notes || "",
      payment_mode: initialData?.payment_mode || "cash",
    },
  });

  const categoryIdValue = watch("category_id");

  // Monitor category dropdown to toggle inline category text input
  useEffect(() => {
    if (categoryIdValue === "NEW_CATEGORY") {
      setIsNewCategoryActive(true);
    } else {
      setIsNewCategoryActive(false);
      setInlineCategoryError("");
    }
  }, [categoryIdValue]);

  const onSubmit = async (values: ExpenseFormValues) => {
    try {
      let finalCategoryId = values.category_id;

      // Handle inline category creation first if active
      if (isNewCategoryActive) {
        const trimmedName = newCategoryName.trim();
        if (!trimmedName) {
          setInlineCategoryError("Category name is required");
          return;
        }
        
        // Call backend to create category on-the-fly
        const newCat = await createCategoryMutation.mutateAsync({ name: trimmedName });
        finalCategoryId = newCat.id;
      }

      const payload = {
        title: values.title.trim(),
        category_id: finalCategoryId,
        amount: Number(values.amount),
        expense_date: values.expense_date,
        notes: values.notes ? values.notes.trim() : null,
        payment_mode: values.payment_mode || null,
      };

      if (isEditMode && initialData) {
        await updateExpenseMutation.mutateAsync({
          id: initialData.id,
          payload,
        });
      } else {
        await createExpenseMutation.mutateAsync(payload);
      }

      if (onSuccess) onSuccess();
    } catch (err: any) {
      const detail = err.message || "Failed to save expense details.";
      setError("root", { type: "server", message: detail });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 animate-fade-in">
      {errors.root && (
        <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/10 border border-destructive/20 p-3.5 rounded-xl">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errors.root.message}</span>
        </div>
      )}

      {/* Title */}
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground font-medium">Expense Title</label>
        <input
          type="text"
          placeholder="e.g. Groceries, Electricity bill"
          maxLength={50}
          {...register("title")}
          className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white placeholder-muted-foreground focus:outline-none transition"
        />
        {errors.title && (
          <p className="text-xs text-destructive mt-1">{errors.title.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Amount */}
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Amount spent (₹)</label>
          <input
            type="number"
            step="0.01"
            placeholder="0.00"
            {...register("amount")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          />
          {errors.amount && (
            <p className="text-xs text-destructive mt-1">{errors.amount.message}</p>
          )}
        </div>

        {/* Date */}
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Expense Date</label>
          <input
            type="date"
            {...register("expense_date")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          />
          {errors.expense_date && (
            <p className="text-xs text-destructive mt-1">{errors.expense_date.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Category Dropdown */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs text-muted-foreground font-medium">Category</label>
          </div>
          <select
            {...register("category_id")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          >
            <option value="" className="bg-zinc-900">-- Select Category --</option>
            {categories?.map((cat) => (
              <option key={cat.id} value={cat.id} className="bg-zinc-900">
                {cat.name}
              </option>
            ))}
            <option value="NEW_CATEGORY" className="bg-zinc-900 font-bold text-primary">
              ➕ Add New Category...
            </option>
          </select>
          {errors.category_id && !isNewCategoryActive && (
            <p className="text-xs text-destructive mt-1">{errors.category_id.message}</p>
          )}
        </div>

        {/* Payment Mode */}
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground font-medium">Payment Mode</label>
          <select
            {...register("payment_mode")}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none transition"
          >
            <option value="cash" className="bg-zinc-900">Cash</option>
            <option value="card" className="bg-zinc-900">Card</option>
            <option value="upi" className="bg-zinc-900">UPI</option>
            <option value="other" className="bg-zinc-900">Other</option>
          </select>
          {errors.payment_mode && (
            <p className="text-xs text-destructive mt-1">{errors.payment_mode.message}</p>
          )}
        </div>
      </div>

      {/* Inline category input */}
      {isNewCategoryActive && (
        <div className="bg-white/5 border border-white/5 p-4 rounded-2xl space-y-2.5 animate-slide-in">
          <div className="flex items-center gap-2 text-xs text-primary font-medium">
            <Tag className="h-3.5 w-3.5" />
            <span>Adding New Category on the fly</span>
          </div>
          <input
            type="text"
            placeholder="Enter new category name (e.g. Subscriptions)"
            maxLength={50}
            value={newCategoryName}
            onChange={(e) => {
              setNewCategoryName(e.target.value);
              setInlineCategoryError("");
            }}
            className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-lg px-3 py-2 text-sm text-white focus:outline-none transition"
          />
          {inlineCategoryError && (
            <p className="text-xs text-destructive">{inlineCategoryError}</p>
          )}
        </div>
      )}

      {/* Notes */}
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground font-medium">Notes (Optional)</label>
        <textarea
          rows={3}
          maxLength={250}
          placeholder="Enter notes about the expense details..."
          {...register("notes")}
          className="w-full bg-white/5 border border-white/10 focus:border-primary rounded-xl px-4 py-2.5 text-sm text-white placeholder-muted-foreground focus:outline-none transition resize-none"
        />
        {errors.notes && (
          <p className="text-xs text-destructive mt-1">{errors.notes.message}</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/5">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2.5 text-xs text-muted-foreground hover:text-white transition"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={createExpenseMutation.isPending || updateExpenseMutation.isPending}
          className="px-5 py-2.5 text-xs font-semibold bg-primary text-black rounded-xl hover:bg-primary/90 transition active:scale-95 disabled:opacity-50"
        >
          {isEditMode ? "Save Changes" : "Log Expense"}
        </button>
      </div>
    </form>
  );
}
export default ExpenseForm;
