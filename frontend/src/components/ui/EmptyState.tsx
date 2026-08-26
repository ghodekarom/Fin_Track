import React from "react";
import { Info } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({
  title = "No data found",
  description = "Get started by adding some records or adjustments.",
  icon = <Info className="h-10 w-10 text-muted-foreground/60" />,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center glass-card rounded-2xl border border-white/5 my-4">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-white/5 mb-4 border border-white/10">
        {icon}
      </div>
      <h3 className="text-lg font-semibold tracking-tight text-white mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6">{description}</p>
      {action && <div className="flex justify-center">{action}</div>}
    </div>
  );
}
export default EmptyState;
