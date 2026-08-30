"use client";

import { useEffect, useState } from "react";
import { fetchDashboardSummary, DashboardSummary } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from "recharts";
import { formatCurrency } from "@/lib/utils";

export default function Home() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardSummary()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-gray-400 animate-pulse">Loading dashboard metrics...</div>;
  }

  if (!data) {
    return <div className="text-red-400">Failed to load dashboard. Make sure backend is running.</div>;
  }

  const { metrics, funnel, actions } = data;

  const summaryCards = [
    { label: "Revenue at Risk", value: formatCurrency(metrics.revenueAtRisk), color: "text-red-400" },
    { label: "Recoverable", value: formatCurrency(metrics.recoverableRevenue), color: "text-amber-400" },
    { label: "Recovery Attempted", value: formatCurrency(metrics.recoveryAttempted), color: "text-blue-400" },
    { label: "Recovered", value: formatCurrency(metrics.revenueRecovered), color: "text-emerald-400" },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Revenue Recovery Overview
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          AI-powered recovery of failed payment revenue
        </p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {summaryCards.map((metric) => (
          <div
            key={metric.label}
            className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors"
          >
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              {metric.label}
            </p>
            <p className={`mt-2 text-2xl font-semibold ${metric.color}`}>
              {metric.value}
            </p>
          </div>
        ))}
        
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors md:col-span-2 lg:col-span-4 flex items-center justify-between">
            <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Recovery Rate</p>
                <p className="mt-2 text-2xl font-semibold text-white">{metrics.recoveryRate}%</p>
            </div>
            <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Cases Processed</p>
                <p className="mt-2 text-2xl font-semibold text-white text-right">{metrics.casesProcessed}</p>
            </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Funnel Chart */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-6">Recovery Funnel</h3>
            <div className="h-64 flex items-center justify-center">
                {funnel.every(f => f.value === 0) ? (
                    <p className="text-sm text-gray-500">No cases processed yet.</p>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={funnel} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                            <XAxis type="number" hide />
                            <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: '#9ca3af', fontSize: 12}} width={120} />
                            <Tooltip cursor={{fill: '#1f2937'}} contentStyle={{backgroundColor: '#111827', borderColor: '#374151', color: '#f3f4f6'}} />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {funnel.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={`hsl(217, 91%, ${60 - index * 8}%)`} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>

        {/* Action Distribution */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-6">Recovery Actions</h3>
            <div className="h-64 flex flex-col items-center justify-center">
                {actions.length === 0 ? (
                    <p className="text-sm text-gray-500">No actions executed yet.</p>
                ) : (
                    <>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={actions} dataKey="count" nameKey="action" cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5}>
                                    {actions.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][index % 4]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{backgroundColor: '#111827', borderColor: '#374151', color: '#f3f4f6'}} />
                            </PieChart>
                        </ResponsiveContainer>
                        <div className="flex justify-center gap-4 mt-4 w-full flex-wrap">
                            {actions.map((a, i) => (
                                <div key={a.action} className="flex items-center gap-2">
                                    <div className="w-3 h-3 rounded-full shrink-0" style={{backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'][i % 4]}}></div>
                                    <span className="text-xs text-gray-400 truncate">{a.action} ({a.count})</span>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>
      </div>
    </div>
  );
}
