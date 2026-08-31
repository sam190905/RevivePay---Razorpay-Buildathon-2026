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
          <h1 className="text-2xl font-bold text-white tracking-tight">Recovery Cases</h1>
          <p className="mt-1 text-sm text-gray-400">All failed payments tracked by RevivePay</p>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-800">
            <thead className="bg-gray-900/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Customer</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Failure</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Score</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Action</th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-right text-xs font-medium text-gray-400 uppercase tracking-wider"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800 bg-transparent">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-gray-500 text-sm">
                    No recovery cases found.
                  </td>
                </tr>
              ) : cases.map((c) => (
                <tr key={c.id} className="relative cursor-pointer hover:bg-gray-800/60 transition-colors duration-150 group focus-within:ring-1 focus-within:ring-blue-500/40">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link href={`/cases/${c.id}`} className="absolute inset-0 z-10 focus:outline-none" aria-label={`View case for ${c.customer_name || 'customer'}`} tabIndex={0} />
                    <div className="text-sm font-medium text-gray-200">{c.customer_name}</div>
                    <div className="text-xs text-gray-500">{c.customer_email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-white">{formatCurrency(c.amount, c.currency)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                    {c.failure_reason}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-300">
                        {c.recovery_probability !== null ? `${(c.recovery_probability * 100).toFixed(0)}%` : '—'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-xs text-gray-400">{c.actual_action || '—'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge status={c.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <svg className="inline-block w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors duration-150" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
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
