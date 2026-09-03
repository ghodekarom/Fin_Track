"use client";

import React, { useState, useEffect } from "react";
import { Download, X, Share, PlusSquare, Sparkles } from "lucide-react";

export default function PwaInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);
  const [isDismissed, setIsDismissed] = useState(true);

  useEffect(() => {
    // 1. Check if already installed / running in standalone mode
    const isStandaloneMode =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as any).standalone === true;

    setIsStandalone(isStandaloneMode);
    if (isStandaloneMode) return;

    // 2. Check if user recently dismissed prompt
    const dismissedUntil = localStorage.getItem("fintrack_pwa_dismissed");
    if (dismissedUntil && new Date().getTime() < Number(dismissedUntil)) {
      return;
    }

    // 3. Detect iOS
    const userAgent = window.navigator.userAgent.toLowerCase();
    const isIosDevice = /iphone|ipad|ipod/.test(userAgent);
    setIsIOS(isIosDevice);

    // 4. Capture beforeinstallprompt on Android / Chromium
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setIsDismissed(false);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);

    // For iOS, show the prompt if not standalone
    if (isIosDevice && !isStandaloneMode) {
      setIsDismissed(false);
    }

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") {
      setIsDismissed(true);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    // Dismiss for 7 days
    const nextWeek = new Date().getTime() + 7 * 24 * 60 * 60 * 1000;
    localStorage.setItem("fintrack_pwa_dismissed", String(nextWeek));
  };

  if (isStandalone || isDismissed) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-sm z-50 animate-in slide-in-from-bottom-5 duration-300">
      <div className="p-4 rounded-2xl bg-card/95 border border-cyan-500/30 backdrop-blur-2xl shadow-2xl shadow-cyan-500/10 flex flex-col gap-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 p-0.5 shadow-md flex items-center justify-center shrink-0">
              <span className="font-extrabold text-white text-base">FT</span>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h4 className="text-xs font-bold text-foreground">
                  Install FinTrack App
                </h4>
                <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300">
                  PWA
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                Operate FinTrack directly on your phone home screen!
              </p>
            </div>
          </div>

          <button
            onClick={handleDismiss}
            className="p-1 text-muted-foreground hover:text-foreground rounded-lg hover:bg-white/10 transition-colors"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Android / Desktop Install Button */}
        {deferredPrompt && (
          <button
            onClick={handleInstallClick}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-zinc-950 font-bold text-xs shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Install on This Device</span>
          </button>
        )}

        {/* iOS Safari Instructions */}
        {isIOS && (
          <div className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-[11px] text-muted-foreground space-y-1 leading-relaxed">
            <p className="flex items-center gap-1.5 text-foreground font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              To install on iPhone:
            </p>
            <p className="flex items-center gap-1.5 ml-1">
              1. Tap the <Share className="w-3.5 h-3.5 text-cyan-400 inline" /> <strong>Share</strong> button in Safari.
            </p>
            <p className="flex items-center gap-1.5 ml-1">
              2. Scroll down & tap <PlusSquare className="w-3.5 h-3.5 text-cyan-400 inline" /> <strong>Add to Home Screen</strong>.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
