import React from "react";

interface LoadingStateProps {
  variant?: "spinner" | "skeleton" | "grid";
  rows?: number;
}

export function LoadingState({ variant = "spinner", rows = 4 }: LoadingStateProps) {
  if (variant === "skeleton") {
    return (
      <div className="w-full space-y-4 animate-pulse p-4">
        <div className="h-8 bg-white/5 rounded-lg w-1/4"></div>
        <div className="space-y-2">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="h-12 bg-white/5 rounded-lg w-full"></div>
          ))}
        </div>
      </div>
    );
  }

  if (variant === "grid") {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse p-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-32 bg-white/5 rounded-2xl w-full border border-white/5"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-[200px] w-full">
      <div className="relative w-12 h-12">
        <div className="absolute top-0 left-0 w-full h-full border-4 border-primary/20 rounded-full"></div>
        <div className="absolute top-0 left-0 w-full h-full border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      </div>
    </div>
  );
}
export default LoadingState;
