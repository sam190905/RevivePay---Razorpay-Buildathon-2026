"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import { Search, X, Loader2, ArrowRight, CheckCircle2, AlertCircle, RotateCw, Ban, CircleDot } from "lucide-react";
import { searchRecoveryCases, RecoveryCase } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

/* ── status helpers ─────────────────────────────────────────────── */

function StatusDot({ status }: { status: string }) {
  const map: Record<string, { color: string; Icon: React.ElementType }> = {
    recovered:         { color: "text-[var(--success)]",   Icon: CheckCircle2 },
    partially_recovered: { color: "text-[var(--success)]", Icon: CheckCircle2 },
    failed:            { color: "text-[var(--danger)]",    Icon: AlertCircle },
    manual_review:     { color: "text-[var(--warning)]",   Icon: Ban },
    processing:        { color: "text-[var(--brand)]",     Icon: RotateCw },
    open:              { color: "text-[var(--brand)]",     Icon: CircleDot },
  };
  const { color, Icon } = map[status] ?? { color: "text-[var(--text-muted)]", Icon: CircleDot };
  return <Icon className={`w-4 h-4 flex-shrink-0 ${color}`} />;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    recovered:           "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20",
    partially_recovered: "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20",
    failed:              "bg-[var(--danger)]/10  text-[var(--danger)]  border-[var(--danger)]/20",
    manual_review:       "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20",
    processing:          "bg-[var(--brand)]/10   text-[var(--brand)]   border-[var(--brand)]/20",
    open:                "bg-[var(--brand)]/10   text-[var(--brand)]   border-[var(--brand)]/20",
  };
  const cls = styles[status] ?? "bg-[var(--surface-overlay)] text-[var(--text-muted)] border-[var(--border-subtle)]";
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold capitalize border ${cls}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

/* ── main component ─────────────────────────────────────────────── */

export function SearchCommand() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  /* ── open / close ──────────────────────────────────────────────── */

  const openPalette = useCallback(() => {
    setOpen(true);
    setQuery("");
    setResults([]);
    setSelected(0);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, []);

  const closePalette = useCallback(() => {
    setOpen(false);
    setQuery("");
    setResults([]);
    setLoading(false);
  }, []);

  /* ── global keyboard shortcut  Ctrl/Cmd+K ─────────────────────── */

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        open ? closePalette() : openPalette();
      }
      if (e.key === "Escape" && open) closePalette();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, openPalette, closePalette]);

  /* ── click outside to close ───────────────────────────────────── */

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        closePalette();
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open, closePalette]);

  /* ── debounced search ─────────────────────────────────────────── */

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) { setResults([]); setLoading(false); return; }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await searchRecoveryCases(query);
        setResults(data);
        setSelected(0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query]);

  /* ── keyboard navigation in results ──────────────────────────── */

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!results.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)); }
    if (e.key === "ArrowUp")   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === "Enter") {
      e.preventDefault();
      navigateTo(results[selected]);
    }
  };

  const navigateTo = (c: RecoveryCase) => {
    closePalette();
    router.push(`/cases/${c.id}`);
  };

  /* ── render ───────────────────────────────────────────────────── */

  return (
    <>
      {/* Topbar trigger button */}
      <button
        id="search-trigger"
        onClick={openPalette}
        className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-[var(--surface)] border border-[var(--border-subtle)] rounded-full text-[var(--text-muted)] text-sm hover:border-[var(--brand)]/40 hover:text-[var(--text-primary)] transition-all duration-200 group"
      >
        <Search className="w-4 h-4 group-hover:text-[var(--brand)] transition-colors" />
        <span className="w-32 text-left">Search anything...</span>
        <span className="text-xs border border-[var(--border-subtle)] rounded px-1 ml-1 bg-[var(--surface-overlay)]">⌘K</span>
      </button>

      {/* Backdrop + Modal */}
      {mounted && open && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-20 px-4">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

          {/* Panel */}
          <div
            ref={containerRef}
            className="relative w-full max-w-xl bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl shadow-2xl overflow-hidden backdrop-blur-xl"
            style={{ boxShadow: "0 25px 60px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.05)" }}
          >
            {/* Input row */}
            <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[var(--border-subtle)]">
              {loading
                ? <Loader2 className="w-5 h-5 text-[var(--brand)] animate-spin flex-shrink-0" />
                : <Search className="w-5 h-5 text-[var(--text-muted)] flex-shrink-0" />
              }
              <input
                ref={inputRef}
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search by customer, email, payment ID, amount, status…"
                className="flex-1 bg-transparent border-none outline-none text-[var(--text-primary)] placeholder-[var(--text-muted)] text-sm"
              />
              {query && (
                <button onClick={() => setQuery("")} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                  <X className="w-4 h-4" />
                </button>
              )}
              <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium text-[var(--text-muted)] border border-[var(--border-subtle)] rounded bg-[var(--surface)] ml-1">
                ESC
              </kbd>
            </div>

            {/* Results */}
            {results.length > 0 && (
              <ul className="max-h-[380px] overflow-y-auto divide-y divide-[var(--border-subtle)]/50 py-1">
                {results.map((c, i) => (
                  <li key={c.id}>
                    <button
                      onClick={() => navigateTo(c)}
                      onMouseEnter={() => setSelected(i)}
                      className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors duration-100 ${
                        selected === i
                          ? "bg-[var(--brand)]/8 border-l-2 border-[var(--brand)]"
                          : "border-l-2 border-transparent hover:bg-[var(--border-subtle)]/40"
                      }`}
                    >
                      <StatusDot status={c.status} />

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-[var(--text-primary)] truncate">
                            {c.customer_name}
                          </span>
                          <StatusBadge status={c.status} />
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-[var(--text-muted)] truncate">{c.customer_email}</span>
                          {c.failure_reason && (
                            <>
                              <span className="text-[var(--border-subtle)]">·</span>
                              <span className="text-xs text-[var(--text-muted)] truncate">{c.failure_reason}</span>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-col items-end flex-shrink-0">
                        <span className="text-sm font-bold text-[var(--text-primary)] tabular-nums">
                          {formatCurrency(c.amount, c.currency)}
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5 truncate max-w-[120px]">
                          {c.id.split("-")[0]}…
                        </span>
                      </div>

                      <ArrowRight className={`w-4 h-4 flex-shrink-0 transition-opacity ${selected === i ? "opacity-100 text-[var(--brand)]" : "opacity-0"}`} />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {/* Empty / idle states */}
            {!loading && query.trim() && results.length === 0 && (
              <div className="px-4 py-10 text-center">
                <Search className="w-8 h-8 text-[var(--text-muted)] mx-auto mb-3 opacity-40" />
                <p className="text-sm font-medium text-[var(--text-secondary)]">No results for &ldquo;{query}&rdquo;</p>
                <p className="text-xs text-[var(--text-muted)] mt-1">Try customer name, email, payment ID, status, or amount</p>
              </div>
            )}

            {!query.trim() && (
              <div className="px-4 py-6">
                <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Quick tips</p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    ["Customer name", "John Doe"],
                    ["Email", "user@example.com"],
                    ["Status", "recovered / failed"],
                    ["Amount", "1000 (in ₹)"],
                    ["Failure reason", "INSUFFICIENT_FUNDS"],
                    ["Case ID", "uuid..."],
                  ].map(([label, example]) => (
                    <div key={label} className="flex flex-col gap-0.5 p-2 rounded-lg bg-[var(--surface)] border border-[var(--border-subtle)]">
                      <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">{label}</span>
                      <span className="text-xs text-[var(--text-secondary)] font-mono">{example}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Footer hint */}
            <div className="flex items-center justify-between px-4 py-2 border-t border-[var(--border-subtle)] bg-[var(--surface)]/50">
              <div className="flex items-center gap-3 text-[10px] text-[var(--text-muted)]">
                <span><kbd className="px-1 border border-[var(--border-subtle)] rounded bg-[var(--surface)]">↑↓</kbd> navigate</span>
                <span><kbd className="px-1 border border-[var(--border-subtle)] rounded bg-[var(--surface)]">↵</kbd> open</span>
                <span><kbd className="px-1 border border-[var(--border-subtle)] rounded bg-[var(--surface)]">esc</kbd> close</span>
              </div>
              {results.length > 0 && (
                <span className="text-[10px] text-[var(--text-muted)]">{results.length} result{results.length !== 1 ? "s" : ""}</span>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
