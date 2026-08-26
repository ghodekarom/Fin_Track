"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Receipt, Tags, Menu, X, Landmark } from "lucide-react";
import clsx from "clsx";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Expenses", href: "/expenses", icon: Receipt },
    { name: "Categories", href: "/categories", icon: Tags },
  ];

  const toggleMobileMenu = () => setMobileMenuOpen(!mobileMenuOpen);
  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col md:flex-row">
      {/* Side Navigation (Desktop) */}
      <aside className="hidden md:flex flex-col w-64 border-r border-white/5 bg-black/20 backdrop-blur-md shrink-0">
        {/* Brand Logo Header */}
        <div className="flex items-center gap-3 px-6 py-6 border-b border-white/5">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-emerald-400 text-black shadow-lg shadow-primary/20">
            <Landmark className="h-5 w-5" />
          </div>
          <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-white to-neutral-400 bg-clip-text text-transparent">
            FinTrack
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-6 px-4 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group",
                  isActive
                    ? "bg-primary text-black font-semibold shadow-md shadow-primary/10"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                )}
              >
                <Icon
                  className={clsx(
                    "h-5 w-5 shrink-0 transition-transform duration-200 group-hover:scale-105",
                    isActive ? "text-black" : "text-muted-foreground group-hover:text-white"
                  )}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Footer info */}
        <div className="p-4 border-t border-white/5 text-center">
          <p className="text-xs text-muted-foreground/40">FinTrack v1.0.0</p>
        </div>
      </aside>

      {/* Header & Body Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header (Mobile menu trigger + branding) */}
        <header className="flex items-center justify-between px-6 py-4 md:py-6 border-b border-white/5 bg-black/10 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center gap-3 md:hidden">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-emerald-400 text-black shadow-md">
              <Landmark className="h-4 w-4" />
            </div>
            <span className="font-bold text-lg tracking-tight text-white">FinTrack</span>
          </div>

          {/* Desktop Title Header */}
          <h1 className="hidden md:block font-semibold text-lg tracking-wide text-neutral-300">
            {pathname.startsWith("/expenses")
              ? "Expenses Ledger"
              : pathname.startsWith("/categories")
              ? "Categories Management"
              : "Financial Overview"}
          </h1>

          {/* Mobile Menu Button */}
          <button
            onClick={toggleMobileMenu}
            className="md:hidden p-2 rounded-lg bg-white/5 text-muted-foreground hover:text-white hover:bg-white/10 transition-colors border border-white/5"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </header>

        {/* Mobile Navigation Drawer Overlay */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-50 flex">
            {/* Backdrop */}
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={closeMobileMenu} />

            {/* Content panel */}
            <div className="relative flex flex-col w-4/5 max-w-sm bg-background border-r border-white/10 p-6 animate-slide-in">
              <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-primary to-emerald-400 text-black shadow-md">
                    <Landmark className="h-4 w-4" />
                  </div>
                  <span className="font-bold text-lg text-white">FinTrack</span>
                </div>
                <button
                  onClick={closeMobileMenu}
                  className="p-1 rounded-lg bg-white/5 text-muted-foreground hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <nav className="flex-1 space-y-2">
                {navigation.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={closeMobileMenu}
                      className={clsx(
                        "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                        isActive ? "bg-primary text-black font-semibold" : "text-muted-foreground hover:text-white"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>

              <div className="text-center pt-4 border-t border-white/5">
                <p className="text-xs text-muted-foreground/40">FinTrack v1.0.0</p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto px-4 md:px-8 py-6 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
export default AppShell;
