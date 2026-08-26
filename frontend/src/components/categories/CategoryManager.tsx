"use client";

import React, { useState } from "react";
import {
  useCategories,
  useCreateCategory,
  useRenameCategory,
  useDeleteCategory,
} from "../../lib/queries/categories";
import { LoadingState } from "../ui/LoadingState";
import { ErrorState } from "../ui/ErrorState";
import { Trash2, Edit2, Check, X, AlertTriangle, Plus } from "lucide-react";

export function CategoryManager() {
  const { data: categories, isLoading, isError, refetch } = useCategories();
  const createMutation = useCreateCategory();
  const renameMutation = useRenameCategory();
  const deleteMutation = useDeleteCategory();

  // Create state
  const [newCategoryName, setNewCategoryName] = useState("");
  const [createError, setCreateError] = useState("");

  // Rename state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");
  const [renameError, setRenameError] = useState("");

  // Delete state
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteMode, setDeleteMode] = useState<"choose" | "reassign" | "cascade" | null>(null);
  const [reassignTargetId, setReassignTargetId] = useState("");
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleteError, setDeleteError] = useState("");

  // Handle creation
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError("");
    const trimmed = newCategoryName.trim();
    if (!trimmed) {
      setCreateError("Name cannot be empty");
      return;
    }
    try {
      await createMutation.mutateAsync({ name: trimmed });
      setNewCategoryName("");
    } catch (err: any) {
      setCreateError(err.message || "Failed to create category");
    }
  };

  // Handle rename initiation
  const startRename = (id: string, currentName: string) => {
    setEditingId(id);
    setEditingName(currentName);
    setRenameError("");
  };

  // Save rename
  const handleRename = async (id: string) => {
    setRenameError("");
    const trimmed = editingName.trim();
    if (!trimmed) {
      setRenameError("Name cannot be empty");
      return;
    }
    try {
      await renameMutation.mutateAsync({ id, name: trimmed });
      setEditingId(null);
    } catch (err: any) {
      setRenameError(err.message || "Failed to rename category");
    }
  };

  // Open delete wizard
  const startDelete = (id: string, expenseCount: number) => {
    setDeletingId(id);
    setDeleteError("");
    if (expenseCount === 0) {
      // Direct delete since no expenses are linked
      setDeleteMode("cascade");
    } else {
      setDeleteMode("choose");
      setReassignTargetId("");
      setDeleteConfirmText("");
    }
  };

  // Finalize delete
  const handleDeleteConfirm = async () => {
    if (!deletingId) return;
    setDeleteError("");

    try {
      if (deleteMode === "reassign") {
        if (!reassignTargetId) {
          setDeleteError("Please select a target category");
          return;
        }
        await deleteMutation.mutateAsync({
          id: deletingId,
          reassign_to: reassignTargetId,
          force: false,
        });
      } else if (deleteMode === "cascade") {
        const category = categories?.find((c) => c.id === deletingId);
        const hasExpenses = (category?.expense_count ?? 0) > 0;
        
        if (hasExpenses && deleteConfirmText.toLowerCase() !== "delete") {
          setDeleteError("Please type 'delete' to confirm cascade removal");
          return;
        }
        await deleteMutation.mutateAsync({
          id: deletingId,
          force: true,
        });
      }
      // Reset delete wizard
      setDeletingId(null);
      setDeleteMode(null);
    } catch (err: any) {
      setDeleteError(err.message || "Failed to delete category");
    }
  };

  if (isLoading) return <LoadingState variant="skeleton" />;
  if (isError) return <ErrorState onRetry={refetch} />;

  const deletingCategory = categories?.find((c) => c.id === deletingId);
  const otherCategories = categories?.filter((c) => c.id !== deletingId) || [];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Create form */}
      <form onSubmit={handleCreate} className="glass-card p-6 rounded-2xl border border-white/5 space-y-4">
        <h2 className="text-md font-semibold text-white">Create New Category</h2>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <input
              type="text"
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              placeholder="e.g. Shopping, Subscriptions, Fitness"
              maxLength={50}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-muted-foreground focus:outline-none focus:border-primary transition"
            />
            {createError && <p className="text-xs text-destructive mt-1.5">{createError}</p>}
          </div>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-medium text-black bg-primary hover:bg-primary/90 disabled:opacity-50 rounded-xl transition duration-150 active:scale-95 shrink-0"
          >
            <Plus className="h-4 w-4" />
            Add Category
          </button>
        </div>
      </form>

      {/* Grid of categories */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories?.map((category) => {
          const isEditing = editingId === category.id;
          return (
            <div
              key={category.id}
              className="glass-card p-5 rounded-2xl border border-white/5 flex flex-col justify-between glass-card-hover min-h-[140px]"
            >
              {isEditing ? (
                // Editing view
                <div className="space-y-3 w-full">
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    maxLength={50}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-primary transition"
                  />
                  {renameError && <p className="text-xs text-destructive">{renameError}</p>}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRename(category.id)}
                      disabled={renameMutation.isPending}
                      className="p-1.5 rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="p-1.5 rounded-lg bg-white/5 text-muted-foreground hover:bg-white/10 transition"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ) : (
                // Standard view
                <div className="w-full">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-white truncate max-w-[80%]">
                      {category.name}
                    </h3>
                    {category.is_default && (
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-white/5 text-neutral-400 border border-white/5 shrink-0">
                        Default
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {category.expense_count} {category.expense_count === 1 ? "expense" : "expenses"} logged
                  </p>
                </div>
              )}

              {/* Actions footer */}
              {!isEditing && (
                <div className="flex items-center justify-end gap-2 mt-4 pt-3 border-t border-white/5">
                  <button
                    onClick={() => startRename(category.id, category.name)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white transition"
                    title="Rename category"
                  >
                    <Edit2 className="h-3.5 w-3.5" />
                  </button>
                  {!category.is_default && (
                    <button
                      onClick={() => startDelete(category.id, category.expense_count)}
                      className="p-2 rounded-lg bg-destructive/10 hover:bg-destructive/20 text-destructive transition"
                      title="Delete category"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Delete Wizard Modal */}
      {deletingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/75 backdrop-blur-sm"
            onClick={() => {
              setDeletingId(null);
              setDeleteMode(null);
            }}
          />

          {/* Modal Container */}
          <div className="relative glass-card border border-white/10 p-6 rounded-3xl w-full max-w-md bg-zinc-950 shadow-2xl space-y-6">
            <div className="flex items-center gap-3 text-destructive">
              <AlertTriangle className="h-6 w-6 shrink-0" />
              <h3 className="text-lg font-semibold text-white">Delete Category</h3>
            </div>

            <p className="text-sm text-neutral-300">
              You are about to delete <span className="font-semibold text-white">"{deletingCategory?.name}"</span>.
            </p>

            {deleteMode === "choose" && (
              <div className="space-y-4">
                <div className="bg-destructive/10 border border-destructive/20 p-4 rounded-xl text-xs text-neutral-300">
                  This category contains <span className="font-semibold text-white">{deletingCategory?.expense_count}</span> linked expense(s). Removing it directly will orphan or delete these records.
                </div>
                <div className="space-y-2.5">
                  <button
                    onClick={() => setDeleteMode("reassign")}
                    className="w-full text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-sm text-white font-medium transition"
                  >
                    👉 Reassign expenses to another category
                  </button>
                  <button
                    onClick={() => setDeleteMode("cascade")}
                    className="w-full text-left px-4 py-3 rounded-xl bg-destructive/10 border border-destructive/20 hover:bg-destructive/20 text-sm text-destructive font-medium transition"
                  >
                    ⚠️ Force delete category & all its expenses
                  </button>
                </div>
              </div>
            )}

            {deleteMode === "reassign" && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs text-muted-foreground font-medium">
                    Move all linked expenses to:
                  </label>
                  <select
                    value={reassignTargetId}
                    onChange={(e) => setReassignTargetId(e.target.value)}
                    className="w-full bg-white/5 border border-white/15 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary transition"
                  >
                    <option value="" className="bg-zinc-900">-- Select Category --</option>
                    {otherCategories.map((c) => (
                      <option key={c.id} value={c.id} className="bg-zinc-900">
                        {c.name} ({c.expense_count})
                      </option>
                    ))}
                  </select>
                </div>
                {deleteError && <p className="text-xs text-destructive">{deleteError}</p>}
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setDeleteMode("choose")}
                    className="px-4 py-2 text-xs text-muted-foreground hover:text-white"
                  >
                    Back
                  </button>
                  <button
                    onClick={handleDeleteConfirm}
                    disabled={deleteMutation.isPending}
                    className="px-5 py-2.5 text-xs font-semibold bg-primary text-black rounded-xl hover:bg-primary/90 transition active:scale-95"
                  >
                    Reassign & Delete
                  </button>
                </div>
              </div>
            )}

            {deleteMode === "cascade" && (
              <div className="space-y-4">
                {(deletingCategory?.expense_count ?? 0) > 0 && (
                  <div className="space-y-3">
                    <p className="text-xs text-destructive font-semibold">
                      CRITICAL: This will also permanently delete all {deletingCategory?.expense_count} expense records associated with this category.
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Type <span className="font-bold text-white uppercase">delete</span> below to confirm:
                    </p>
                    <input
                      type="text"
                      value={deleteConfirmText}
                      onChange={(e) => setDeleteConfirmText(e.target.value)}
                      placeholder="Type delete to confirm"
                      className="w-full bg-white/5 border border-destructive/20 focus:border-destructive rounded-xl px-4 py-2.5 text-sm text-white placeholder-muted-foreground/40 focus:outline-none transition"
                    />
                  </div>
                )}
                {deleteError && <p className="text-xs text-destructive">{deleteError}</p>}
                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => {
                      if ((deletingCategory?.expense_count ?? 0) > 0) {
                        setDeleteMode("choose");
                      } else {
                        setDeletingId(null);
                        setDeleteMode(null);
                      }
                    }}
                    className="px-4 py-2 text-xs text-muted-foreground hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteConfirm}
                    disabled={deleteMutation.isPending}
                    className="px-5 py-2.5 text-xs font-semibold bg-destructive text-white rounded-xl hover:bg-destructive/95 transition active:scale-95"
                  >
                    Force Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
export default CategoryManager;
