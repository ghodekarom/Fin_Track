"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  Check,
  X,
  Loader2,
  Calendar,
  CreditCard,
  Tag,
  FileText,
  Zap,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { ParsedExpenseDraft } from "@/types/ai";

interface QuickAddExpenseBarProps {
  onExpenseAdded?: () => void;
}

export default function QuickAddExpenseBar({ onExpenseAdded }: QuickAddExpenseBarProps) {
  const [inputText, setInputText] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [draft, setDraft] = useState<ParsedExpenseDraft | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleParse = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputText.trim();
    if (!text || isParsing) return;

    setIsParsing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await apiClient.post<ParsedExpenseDraft>("/ai/quick-add/parse", {
        text,
      });
      setDraft(res.data);
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message ||
        err?.message ||
        "Could not parse expense string. Please try again."
      );
    } finally {
      setIsParsing(false);
    }
  };

  const handleConfirmSave = async () => {
    if (!draft || isSaving) return;
    setIsSaving(true);
    setErrorMessage(null);

    try {
      await apiClient.post("/ai/quick-add/confirm", {
        title: draft.title,
        amount: draft.amount,
        category_id: draft.category_id,
        expense_date: draft.expense_date,
        payment_mode: draft.payment_mode,
        notes: draft.notes,
      });

      setSuccessMessage(`Saved: ₹${draft.amount.toLocaleString("en-IN")} for ${draft.title}!`);
      setDraft(null);
      setInputText("");

      if (onExpenseAdded) {
        onExpenseAdded();
      }

      setTimeout(() => {
        setSuccessMessage(null);
      }, 4000);
    } catch (err: any) {
      setErrorMessage(
        err?.response?.data?.error?.message ||
        err?.message ||
        "Failed to save expense."
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelDraft = () => {
    setDraft(null);
  };

  return (
    <div className="relative overflow-hidden bg-card/60 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-5 shadow-lg transition-all duration-300">
      {/* Glow backdrop */}
      <div className="absolute top-0 right-0 -mr-12 -mt-12 w-40 h-40 rounded-full bg-cyan-500/10 blur-2xl pointer-events-none" />

      {/* Input Row */}
      <form onSubmit={handleParse} className="space-y-3">
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              <Sparkles className="w-3.5 h-3.5" />
            </span>
            <span className="text-xs font-bold text-foreground">
              Natural Language Quick-Add
            </span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/25 hidden sm:inline">
              Smart Auto-Categorizer
            </span>
          </div>
          <span className="text-[11px] text-muted-foreground hidden sm:inline">
            Type naturally: amount, merchant, date, payment mode
          </span>
        </div>

        <div className="flex items-center gap-2 bg-background/80 border border-white/10 rounded-xl px-3 py-1.5 focus-within:border-cyan-500/60 focus-within:ring-1 focus-within:ring-cyan-500/20 transition-all">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="e.g. Spent 450 on Uber to office yesterday via upi..."
            disabled={isParsing || isSaving}
            className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground focus:outline-none py-1"
          />

          <button
            type="submit"
            disabled={isParsing || isSaving || !inputText.trim()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-cyan-500 hover:bg-cyan-400 text-zinc-950 disabled:opacity-40 transition-all cursor-pointer shadow-sm shrink-0"
          >
            {isParsing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Parsing...</span>
              </>
            ) : (
              <>
                <span>AI Parse</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Success Notification */}
      {successMessage && (
        <div className="mt-3 p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Error Notification */}
      {errorMessage && (
        <div className="mt-3 p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-2 animate-in fade-in">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Interactive Parsed Draft Preview Card */}
      {draft && (
        <div className="mt-3.5 p-4 rounded-xl bg-background/90 border border-cyan-500/30 shadow-lg animate-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              <h4 className="text-xs font-bold text-foreground">
                Extracted Expense Draft Preview
              </h4>
              <span className="text-[10px] text-muted-foreground">
                ({Math.round(draft.confidence_score * 100)}% confidence)
              </span>
            </div>
            <button
              onClick={handleCancelDraft}
              className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-white/10"
              title="Discard draft"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {/* Title */}
            <div>
              <span className="text-[10px] uppercase font-semibold text-muted-foreground block mb-0.5">
                Item / Merchant
              </span>
              <span className="font-bold text-foreground truncate block">
                {draft.title}
              </span>
            </div>

            {/* Amount */}
            <div>
              <span className="text-[10px] uppercase font-semibold text-muted-foreground block mb-0.5">
                Amount
              </span>
              <span className="font-bold text-emerald-400 block">
                ₹{draft.amount.toLocaleString("en-IN")}
              </span>
            </div>

            {/* Category */}
            <div>
              <span className="text-[10px] uppercase font-semibold text-muted-foreground block mb-0.5">
                Category
              </span>
              <span className="inline-block px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-300 border border-cyan-500/25 text-[11px] font-medium">
                {draft.category_name}
              </span>
            </div>

            {/* Date & Payment */}
            <div>
              <span className="text-[10px] uppercase font-semibold text-muted-foreground block mb-0.5">
                Date & Mode
              </span>
              <span className="text-muted-foreground text-[11px] block">
                {draft.expense_date} • <strong className="uppercase text-foreground">{draft.payment_mode}</strong>
              </span>
            </div>
          </div>

          {draft.notes && (
            <p className="text-[11px] text-muted-foreground mt-2 italic">
              Notes: {draft.notes}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 mt-4 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={handleCancelDraft}
              disabled={isSaving}
              className="px-3 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground bg-white/5 hover:bg-white/10 rounded-lg transition-all cursor-pointer"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleConfirmSave}
              disabled={isSaving}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500 hover:bg-emerald-400 text-zinc-950 transition-all cursor-pointer shadow-md shadow-emerald-500/20"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Confirm & Save Expense</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
