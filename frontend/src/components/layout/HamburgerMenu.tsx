"use client";

import React from "react";
import { Menu } from "lucide-react";

interface HamburgerMenuProps {
  onToggle: () => void;
  isOpen: boolean;
}

export function HamburgerMenu({ onToggle, isOpen }: HamburgerMenuProps) {
  return (
    <button
      onClick={onToggle}
      className="md:hidden p-2 rounded-lg bg-white/5 text-muted-foreground hover:text-white hover:bg-white/10 transition-colors border border-white/5"
      aria-label={isOpen ? "Close menu" : "Open menu"}
    >
      <Menu className="h-5 w-5" />
    </button>
  );
}
export default HamburgerMenu;
