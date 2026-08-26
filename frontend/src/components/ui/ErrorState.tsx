import React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message = "Failed to load data from the server. Check your connection or retry.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-6 text-center border border-destructive/20 bg-destructive/5 rounded-2xl max-w-lg mx-auto my-6">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-destructive/10 text-destructive mb-4">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-md font-semibold text-destructive mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground mb-6 max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-destructive hover:bg-destructive/90 rounded-xl transition duration-150 active:scale-95"
        >
          <RotateCcw className="h-4 w-4" />
          Retry Request
        </button>
      )}
    </div>
  );
}
export default ErrorState;
