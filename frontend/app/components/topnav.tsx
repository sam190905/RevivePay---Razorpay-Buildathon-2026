"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Files, Settings, Bell, Sun, Moon, Menu } from "lucide-react";
import { useTheme } from "./theme-provider";
import { SearchCommand } from "./search-command";

export function TopNav() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { name: "Overview",       href: "/",      icon: LayoutDashboard },
    { name: "Recovery Cases", href: "/cases", icon: Files },
    { name: "Demo Control",   href: "/demo",  icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[var(--border-subtle)] bg-[var(--surface-overlay)] backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-6">

        {/* Left: Logo */}
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--brand)] text-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <span className="text-lg font-bold text-[var(--text-primary)]">RevivePay</span>
        </div>

        {/* Center: Main Navigation */}
        <nav className="hidden md:flex items-center space-x-1 p-1 bg-[var(--surface)] border border-[var(--border-subtle)] rounded-full shadow-[var(--shadow-glow)]">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-[var(--brand)] text-white shadow-md"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--border-subtle)]"
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* Right: Search + Controls + Profile */}
        <div className="flex items-center gap-4">

          {/* Search command palette */}
          <SearchCommand />

          <button
            onClick={toggleTheme}
            className="p-2 rounded-full text-[var(--text-secondary)] hover:bg-[var(--surface)] hover:text-[var(--text-primary)] transition-colors border border-transparent hover:border-[var(--border-subtle)]"
            aria-label="Toggle theme"
          >
            {theme === "light" ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>

          <button className="relative p-2 rounded-full text-[var(--text-secondary)] hover:bg-[var(--surface)] hover:text-[var(--text-primary)] transition-colors border border-transparent hover:border-[var(--border-subtle)]">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-2 w-2 h-2 bg-[var(--brand)] rounded-full border border-white dark:border-gray-900"></span>
          </button>

          <div className="hidden sm:flex items-center gap-3 pl-2 border-l border-[var(--border-subtle)]">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-[var(--brand)] font-semibold text-sm">
              A
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-[var(--text-primary)] leading-tight">Admin</span>
              <span className="text-[10px] text-[var(--text-muted)] leading-tight">Administrator</span>
            </div>
          </div>

          <button className="md:hidden p-2 text-[var(--text-secondary)]">
            <Menu className="w-6 h-6" />
          </button>
        </div>

      </div>
    </header>
  );
}
