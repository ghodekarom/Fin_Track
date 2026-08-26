"use client";

import React from "react";
import { CategoryManager } from "@/components/categories/CategoryManager";
import { Tags } from "lucide-react";

export default function CategoriesPage() {
  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Tags className="h-6 w-6 text-primary" />
          Categories Management
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Create, rename, or safely delete categories. Default categories cannot be removed.
        </p>
      </div>

      <CategoryManager />
    </div>
  );
}
