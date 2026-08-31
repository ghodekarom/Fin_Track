"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Receipt,
  Tags,
  Menu,
  X,
  Landmark,
  LogOut,
  ShieldAlert,
  User as UserIcon,
  ChevronDown,
  Loader2,
} from "lucide-react";
import clsx from "clsx";
import { useAuth } from "@/hooks/useAuth";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout, logoutAll } = useAuth();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const isAuthPage =
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/forgot-password") ||
    pathname.startsWith("/reset-password");

  // Route protection redirect
  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated && !isAuthPage) {
        router.push("/login");
      } else if (isAuthenticated && isAuthPage) {
        router.push("/dashboard");
      }
    }
  }, [isAuthenticated, isLoading, isAuthPage, router]);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
      router.push("/login");
    } finally {
      setLoggingOut(false);
      setProfileDropdownOpen(false);
    }
  };

  const handleLogoutAll = async () => {
    setLoggingOut(true);
    try {
      await logoutAll();
      router.push("/login");
    } finally {
      setLoggingOut(false);
      setProfileDropdownOpen(false);
    }
  };

  // If on Auth pages, render clean layout without navigation chrome
  if (isAuthPage) {
    return <main className="min-h-screen bg-background">{children}</main>;
  }

  // Loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
        <p className="text-sm text-muted-foreground animate-pulse">Initializing FinTrack...</p>
      </div>
    );
  }

  // If not authenticated and waiting for redirect
  if (!isAuthenticated) {
    return null;
  }

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Expenses", href: "/expenses", icon: Receipt },
    { name: "Categories", href: "/categories", icon: Tags },
  ];

  const toggleMobileMenu = () => setMobileMenuOpen(!mobileMenuOpen);
  const closeMobileMenu = () => setMobileMenuOpen(false);

  const userInitial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : user?.email
    ? user.email.charAt(0).toUpperCase()
    : "U";

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col md:flex-row">
      {/* Side Navigation (Desktop) */}
      <aside className="hidden md:flex flex-col w-64 border-r border-white/5 bg-black/20 backdrop-blur-md shrink-0">
        {/* Brand Logo Header */}
        <div className="flex items-center gap-3 px-6 py-6 border-b border-white/5">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-black shadow-lg shadow-emerald-500/20">
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
                    ? "bg-emerald-500 text-zinc-950 font-semibold shadow-md shadow-emerald-500/10"
                    : "text-muted-foreground hover:text-white hover:bg-white/5"
                )}
              >
                <Icon
                  className={clsx(
                    "h-5 w-5 shrink-0 transition-transform duration-200 group-hover:scale-105",
                    isActive ? "text-zinc-950" : "text-muted-foreground group-hover:text-white"
                  )}
                />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User Account / Profile Section in Sidebar */}
        <div className="p-4 border-t border-white/5">
          <div className="relative">
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="w-full flex items-center justify-between p-2 rounded-xl bg-white/5 hover:bg-white/10 transition-colors border border-white/5 text-left"
            >
              <div className="flex items-center gap-3 overflow-hidden">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.full_name || "User"}
                    className="w-8 h-8 rounded-lg object-cover shrink-0"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 font-bold flex items-center justify-center text-sm shrink-0">
                    {userInitial}
                  </div>
                )}
                <div className="overflow-hidden">
                  <p className="text-xs font-semibold text-white truncate">
                    {user?.full_name || user?.email?.split("@")[0]}
                  </p>
                  <p className="text-[11px] text-muted-foreground truncate">{user?.email}</p>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" />
            </button>

            {/* Profile Dropdown Popup */}
            {profileDropdownOpen && (
              <div className="absolute bottom-full left-0 w-full mb-2 bg-card border border-white/10 rounded-xl p-1.5 shadow-2xl shadow-black/80 backdrop-blur-xl z-50 animate-in fade-in slide-in-from-bottom-2">
                <button
                  onClick={handleLogout}
                  disabled={loggingOut}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-red-400 hover:bg-red-500/10 rounded-lg transition-colors text-left"
                >
                  <LogOut className="w-4 h-4 shrink-0" />
                  <span>Log Out</span>
                </button>
                <button
                  onClick={handleLogoutAll}
                  disabled={loggingOut}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-muted-foreground hover:text-white hover:bg-white/5 rounded-lg transition-colors text-left"
                >
                  <ShieldAlert className="w-4 h-4 shrink-0" />
                  <span>Log Out All Devices</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Header & Body Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="flex items-center justify-between px-6 py-4 md:py-6 border-b border-white/5 bg-black/10 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center gap-3 md:hidden">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 text-black shadow-md">
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

          {/* User Quick Info + Mobile Menu Button */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground bg-white/5 border border-white/5 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{user?.email}</span>
            </div>

            <button
              onClick={toggleMobileMenu}
              className="md:hidden p-2 rounded-lg bg-white/5 text-muted-foreground hover:text-white hover:bg-white/10 transition-colors border border-white/5"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-50 flex">
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={closeMobileMenu} />

            <div className="relative flex flex-col w-4/5 max-w-sm bg-background border-r border-white/10 p-6 animate-slide-in">
              <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 text-black shadow-md">
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

              {/* User info in mobile drawer */}
              <div className="mb-6 p-3 rounded-xl bg-white/5 border border-white/5">
                <p className="text-xs font-semibold text-white truncate">
                  {user?.full_name || "Account"}
                </p>
                <p className="text-[11px] text-muted-foreground truncate">{user?.email}</p>
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
                        isActive ? "bg-emerald-500 text-zinc-950 font-semibold" : "text-muted-foreground hover:text-white"
                      )}
                    >
                      <Icon className="h-5 w-5" />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>

              <div className="pt-4 border-t border-white/5 space-y-2">
                <button
                  onClick={() => {
                    closeMobileMenu();
                    handleLogout();
                  }}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-xs font-medium text-red-400 hover:bg-red-500/10 rounded-xl transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Log Out
                </button>
                <button
                  onClick={() => {
                    closeMobileMenu();
                    handleLogoutAll();
                  }}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-xs font-medium text-muted-foreground hover:text-white hover:bg-white/5 rounded-xl transition-colors"
                >
                  <ShieldAlert className="w-4 h-4" />
                  Log Out All Devices
                </button>
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
