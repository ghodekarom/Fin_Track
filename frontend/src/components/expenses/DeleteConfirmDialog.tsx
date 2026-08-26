"use client";

import React from "react";
import { AlertCircle } from "lucide-react";

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  title?: string;
  isDeleting?: boolean;
}

export function DeleteConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  title = "Delete Expense Record",
  isDeleting = false,
}: DeleteConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop overlay */}
      <div className="fixed inset-0 bg-black/75 backdrop-blur-sm" onClick={onCancel} />

      {/* Dialog container */}
      <div className="relative glass-card border border-white/10 p-6 rounded-3xl w-full max-w-sm bg-zinc-950 shadow-2xl space-y-5 animate-scale-up">
        <div className="flex items-center gap-3 text-destructive">
          <AlertCircle className="h-6 w-6 shrink-0" />
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>

        <p className="text-sm text-neutral-300 leading-relaxed">
          Are you sure you want to delete this expense record? This action is permanent and cannot be undone.
        </p>

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2.5 text-xs text-muted-foreground hover:text-white transition"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-5 py-2.5 text-xs font-semibold bg-destructive hover:bg-destructive/90 text-white rounded-xl transition duration-150 active:scale-95 disabled:opacity-50"
          >
            {isDeleting ? "Deleting..." : "Delete Permanently"}
          </button>
        </div>
      </div>
    </div>
  );
}
export default DeleteConfirmDialog;
