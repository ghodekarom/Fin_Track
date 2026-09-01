"use client";

import React from "react";
import { WifiOff, RefreshCw, Home, ShieldX } from "lucide-react";
import Link from "next/link";

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload();
  };

  const handleResetCache = async () => {
    if (typeof window !== "undefined") {
      if ("serviceWorker" in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        for (const registration of registrations) {
          await registration.unregister();
        }
      }
      if ("caches" in window) {
        const keys = await caches.keys();
        for (const key of keys) {
          await caches.delete(key);
        }
      }
      window.location.href = "/login";
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md glass-card rounded-3xl p-8 text-center border border-white/5 relative overflow-hidden bg-card/80 backdrop-blur-xl">
        {/* Glow effect */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Icon */}
        <div className="mx-auto w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-primary mb-6 animate-pulse">
          <WifiOff className="h-8 w-8 text-emerald-400" />
        </div>

        {/* Title & Desc */}
        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">
          You are currently offline
        </h2>
        <p className="text-sm text-muted-foreground mb-8 max-w-sm mx-auto">
          FinTrack needs an active connection to load this page. Please ensure the backend server is running on port 8000.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <button
            onClick={handleRetry}
            className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 text-zinc-950 font-semibold text-sm hover:bg-emerald-400 transition-all duration-200 shadow-md shadow-emerald-500/10 active:scale-95"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>

          <button
            onClick={handleResetCache}
            className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-white/5 text-white border border-white/10 font-semibold text-sm hover:bg-white/10 transition-all duration-200 active:scale-95"
          >
            <ShieldX className="h-4 w-4 text-emerald-400" />
            Reset & Go to Login
          </button>
        </div>
      </div>
    </div>
  );
}
