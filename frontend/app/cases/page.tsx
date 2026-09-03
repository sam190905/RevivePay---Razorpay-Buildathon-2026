"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchRecoveryCases, RecoveryCase } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Badge } from "@/components/badge";

export default function CasesPage() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);

  const loadCases = () => {
    fetchRecoveryCases()
      .then(setCases)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCases();
  }, []);

  useEffect(() => {
    const hasActiveCases = cases.some((c) => c.status === "open" || c.status === "processing");
    if (hasActiveCases) {
      const interval = setInterval(loadCases, 2000);
      return () => clearInterval(interval);
    }
  }, [cases]);

  if (loading) {
    return <div className="text-gray-400 animate-pulse">Loading recovery cases...</div>;
  }

  return (
    <div>
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
            Recovery Cases
            <span className="text-[var(--brand)]">✦</span>
          </h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">All failed payments tracked by RevivePay</p>
        </div>
      </div>

      <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[var(--border-subtle)]">
            <thead className="bg-[var(--surface-overlay)]">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Customer</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Amount</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Failure</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Score</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Action</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)] bg-transparent">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-[var(--text-muted)] text-sm">
                    No recovery cases found.
                  </td>
                </tr>
              ) : cases.map((c) => (
                <tr key={c.id} className="relative cursor-pointer hover:bg-[var(--border-subtle)]/50 transition-all duration-200 group focus-within:ring-1 focus-within:ring-[var(--brand)]/40">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link href={`/cases/${c.id}`} className="absolute inset-0 z-10 focus:outline-none" aria-label={`View case for ${c.customer_name || 'customer'}`} tabIndex={0} />
                    <div className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-[var(--brand)] transition-colors">{c.customer_name}</div>
                    <div className="text-xs text-[var(--text-secondary)]">{c.customer_email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-[var(--text-primary)] tabular-nums">{formatCurrency(c.amount, c.currency)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-[var(--text-primary)] font-medium">
                    {c.failure_reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-[var(--text-primary)]">
                        {c.recovery_probability !== null ? `${(c.recovery_probability * 100).toFixed(0)}%` : '—'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-xs font-medium text-[var(--text-secondary)]">{c.actual_action || '—'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge status={c.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <svg className="inline-block w-5 h-5 text-[var(--text-muted)] group-hover:text-[var(--brand)] group-hover:translate-x-1 transition-all duration-200" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                    </svg>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
