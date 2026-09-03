"use client";

import { useEffect, useState } from "react";
import { fetchDashboardSummary, fetchRecoveryCases, DashboardSummary, RecoveryCase } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, AreaChart, Area } from "recharts";
import { formatCurrency } from "@/lib/utils";
import Link from "next/link";
import { 
  AlertCircle, 
  Wallet, 
  RotateCw, 
  CheckCircle2,
  TrendingUp,
  Database,
  ArrowRight,
  ShieldCheck,
  Cpu,
  CreditCard,
  Network
} from "lucide-react";

export default function Home() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [recentCases, setRecentCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchDashboardSummary(),
      fetchRecoveryCases()
    ])
      .then(([summary, cases]) => {
        setData(summary);
        setRecentCases(cases.slice(0, 5)); // Take top 5
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-gray-400 animate-pulse">Loading dashboard metrics...</div>;
  }

  if (!data) {
    return <div className="text-[var(--danger)]">Failed to load dashboard. Make sure backend is running.</div>;
  }

  const { metrics, funnel, actions } = data;

  const summaryCards = [
    { label: "Revenue at Risk", value: formatCurrency(metrics.revenueAtRisk), color: "text-[var(--danger)]", bg: "bg-[var(--danger)]", icon: AlertCircle },
    { label: "Recoverable", value: formatCurrency(metrics.recoverableRevenue), color: "text-[var(--warning)]", bg: "bg-[var(--warning)]", icon: Wallet },
    { label: "Recovery Attempted", value: formatCurrency(metrics.recoveryAttempted), color: "text-[var(--brand)]", bg: "bg-[var(--brand)]", icon: RotateCw },
    { label: "Recovered", value: formatCurrency(metrics.revenueRecovered), color: "text-[var(--success)]", bg: "bg-[var(--success)]", icon: CheckCircle2 },
  ];

  const getActionColor = (action: string) => {
    if (action.includes("payment_link")) return "var(--brand)";
    if (action.includes("retry")) return "var(--success)";
    if (action.includes("manual")) return "var(--warning)";
    return "var(--text-muted)";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
            Revenue Recovery Overview
            <span className="text-[var(--brand)]">✦</span>
          </h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            AI-powered recovery of failed payment revenue
          </p>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {summaryCards.map((metric) => (
          <div
            key={metric.label}
            className="group bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm hover:shadow-[var(--shadow-glow)] hover:border-[var(--brand)]/30 transition-all duration-300 relative overflow-hidden"
          >
            {/* Subtle glow background */}
            <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full opacity-[0.05] group-hover:opacity-10 transition-opacity duration-300 blur-2xl ${metric.bg}`}></div>
            
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-2 rounded-xl bg-[var(--surface-overlay)] border border-[var(--border-subtle)] shadow-sm ${metric.color}`}>
                <metric.icon className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                {metric.label}
              </p>
            </div>
            <p className="text-3xl font-bold text-[var(--text-primary)] tabular-nums tracking-tight">
              {metric.value}
            </p>
          </div>
        ))}
      </div>
      
      {/* Recovery Rate & Cases Processed */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Recovery Rate */}
        <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-[var(--brand)]/10 text-[var(--brand)]">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Recovery Rate</p>
              <p className="text-2xl font-bold text-[var(--text-primary)] mt-0.5">{metrics.recoveryRate.toFixed(2)}%</p>
            </div>
          </div>
          <div className="w-1/3 max-w-[160px]">
            <div className="h-2 w-full bg-[var(--border-subtle)] rounded-full overflow-hidden">
              <div 
                className="h-full bg-[var(--brand)] rounded-full" 
                style={{ width: `${Math.min(100, Math.max(0, metrics.recoveryRate))}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Cases Processed */}
        <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[var(--border-subtle)] text-[var(--text-primary)]">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Cases Processed</p>
            <p className="text-2xl font-bold text-[var(--text-primary)] mt-0.5">{metrics.casesProcessed}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Funnel Chart */}
        <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm lg:col-span-1">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-6">Recovery Funnel</h3>
            <div className="flex flex-col gap-5">
                {funnel.every(f => f.value === 0) ? (
                    <p className="text-sm text-[var(--text-muted)]">No cases processed yet.</p>
                ) : (
                    funnel.map((step, idx) => {
                      const maxVal = funnel[0]?.value || 1;
                      const percentage = maxVal > 0 ? (step.value / maxVal) * 100 : 0;
                      return (
                        <div key={step.name} className="flex flex-col gap-1.5">
                          <div className="flex justify-between items-center text-xs">
                            <span className="font-medium text-[var(--text-primary)]">{step.name}</span>
                            <span className="font-bold text-[var(--text-primary)] tabular-nums">{step.value}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="flex-1 h-2.5 bg-[var(--border-subtle)] rounded-full overflow-hidden">
                              <div 
                                className="h-full rounded-full transition-all duration-1000 ease-out bg-[var(--brand)]" 
                                style={{ 
                                  width: `${percentage}%`,
                                  opacity: 1 - (idx * 0.15) // Gradually fade the bar as it goes down
                                }}
                              />
                            </div>
                            <span className="text-[10px] text-[var(--text-muted)] w-8 text-right font-medium">
                              {percentage.toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      )
                    })
                )}
            </div>
            {funnel.length > 0 && (
              <p className="text-[10px] text-[var(--text-muted)] mt-6 text-center">Conversion from failed payments to recovered revenue</p>
            )}
        </div>

        {/* Action Distribution */}
        <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm lg:col-span-1">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Recovery Actions</h3>
            <div className="h-64 flex flex-col items-center justify-center relative">
                {actions.length === 0 ? (
                    <p className="text-sm text-[var(--text-muted)]">No actions executed yet.</p>
                ) : (
                    <>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie 
                                  data={actions} 
                                  dataKey="count" 
                                  nameKey="action" 
                                  cx="50%" 
                                  cy="50%" 
                                  innerRadius={70} 
                                  outerRadius={90} 
                                  paddingAngle={3}
                                  stroke="var(--surface)"
                                  strokeWidth={2}
                                >
                                    {actions.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={getActionColor(entry.action)} />
                                    ))}
                                </Pie>
                                <Tooltip 
                                  contentStyle={{
                                    backgroundColor: 'var(--surface-overlay)', 
                                    borderColor: 'var(--border-subtle)', 
                                    color: 'var(--text-primary)',
                                    borderRadius: '8px',
                                    boxShadow: 'var(--shadow-glow)'
                                  }} 
                                  itemStyle={{color: 'var(--text-primary)'}}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        
                        {/* Center text for Donut chart */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none pb-8">
                          <span className="text-2xl font-bold text-[var(--text-primary)]">
                            {actions.reduce((acc, curr) => acc + curr.count, 0)}
                          </span>
                          <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Actions</span>
                        </div>

                        <div className="flex flex-col gap-2 mt-2 w-full pl-4">
                            {actions.map((a, i) => (
                                <div key={a.action} className="flex items-center justify-between group">
                                  <div className="flex items-center gap-2">
                                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{backgroundColor: getActionColor(a.action)}}></div>
                                      <span className="text-xs text-[var(--text-secondary)] font-medium group-hover:text-[var(--text-primary)] transition-colors">{a.action}</span>
                                  </div>
                                  <span className="text-xs font-semibold text-[var(--text-primary)]">{a.count}</span>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>

        {/* Recent Cases */}
        <div className="bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm lg:col-span-1 flex flex-col">
          <div className="flex justify-between items-center mb-5">
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">Recent Cases</h3>
            <Link href="/cases" className="text-xs text-[var(--brand)] font-medium hover:text-[var(--brand-dark)] flex items-center gap-1 transition-colors">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          
          <div className="flex-1 flex flex-col gap-3">
            {recentCases.length === 0 ? (
               <p className="text-sm text-[var(--text-muted)] m-auto">No cases found.</p>
            ) : (
              recentCases.map(c => {
                let statusColor = "bg-[var(--border-subtle)] text-[var(--text-primary)]";
                if (c.status === "recovered" || c.status === "partially_recovered") statusColor = "bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20";
                else if (c.status === "failed") statusColor = "bg-[var(--danger)]/10 text-[var(--danger)] border border-[var(--danger)]/20";
                else if (c.status === "manual_review") statusColor = "bg-[var(--warning)]/10 text-[var(--warning)] border border-[var(--warning)]/20";
                else if (c.status === "processing") statusColor = "bg-[var(--brand)]/10 text-[var(--brand)] border border-[var(--brand)]/20";

                let Icon = c.status === "recovered" ? CheckCircle2 : c.status === "failed" ? AlertCircle : RotateCw;

                return (
                  <Link 
                    key={c.id} 
                    href={`/cases/${c.id}`}
                    className="flex items-center justify-between p-3 rounded-xl border border-transparent hover:bg-[var(--border-subtle)]/50 hover:border-[var(--border-subtle)] transition-all duration-200 group"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${statusColor} bg-transparent border-0`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="text-xs font-semibold text-[var(--text-primary)] font-mono group-hover:text-[var(--brand)] transition-colors">
                          {c.id.split('-')[0]}...
                        </p>
                        <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
                          {formatCurrency(c.amount, c.currency)}
                        </p>
                      </div>
                    </div>
                    <div className={`px-2 py-0.5 rounded text-[10px] font-semibold capitalize ${statusColor}`}>
                      {c.status.replace("_", " ")}
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* System Status Footer */}
      <div className="flex flex-wrap items-center gap-4 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--surface)] shadow-sm">
        <div className="flex items-center gap-2 pr-4 border-r border-[var(--border-subtle)]">
          <ShieldCheck className="w-5 h-5 text-[var(--success)]" />
          <div className="flex flex-col">
            <span className="text-xs font-bold text-[var(--text-primary)]">System Status</span>
            <span className="text-[10px] text-[var(--success)]">All monitored services active</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2 px-2">
          <Cpu className="w-4 h-4 text-[var(--brand)]" />
          <span className="text-xs text-[var(--text-secondary)]">AI Agent</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] ml-1"></div>
        </div>
        
        <div className="flex items-center gap-2 px-2">
          <CreditCard className="w-4 h-4 text-[var(--brand)]" />
          <span className="text-xs text-[var(--text-secondary)]">Razorpay API</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] ml-1"></div>
        </div>

        <div className="flex items-center gap-2 px-2">
          <Network className="w-4 h-4 text-[var(--brand)]" />
          <span className="text-xs text-[var(--text-secondary)]">Webhook Tunnel</span>
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--warning)] ml-1" title="Local tunnel may not be active"></div>
        </div>
      </div>

    </div>
  );
}
