"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchCaseDetail, CaseDetail } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Badge } from "@/components/badge";
import { ArrowLeft, CheckCircle2, Clock, XCircle, AlertCircle, Cpu, Shield, Zap } from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [data, setData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      fetchCaseDetail(params.id as string)
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading) return <div className="text-gray-400 animate-pulse">Loading case details...</div>;
  if (!data) return <div className="text-red-400">Failed to load case.</div>;

  const getEventIcon = (eventType: string, status: string) => {
    if (status === 'failed') return <XCircle className="w-5 h-5 text-red-400" />;
    switch (eventType) {
      case 'case_created': return <AlertCircle className="w-5 h-5 text-blue-400" />;
      case 'ai_diagnosis': return <Cpu className="w-5 h-5 text-purple-400" />;
      case 'policy_check': return <Shield className="w-5 h-5 text-amber-400" />;
      case 'action_executed': return <Zap className="w-5 h-5 text-blue-400" />;
      case 'verification': return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="max-w-5xl">
      <button 
        onClick={() => router.back()} 
        className="mb-6 flex items-center text-sm text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Cases
      </button>

      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            Case Details
            <Badge status={data.case.status} />
          </h1>
          <p className="mt-1 text-sm text-gray-400 font-mono">{data.case.id}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500 uppercase tracking-wider font-medium">Amount at Risk</p>
          <p className="text-2xl font-semibold text-white">{formatCurrency(data.case.amount_at_risk, data.payment.currency)}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
            {/* Overview Card */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider text-gray-500">Overview</h3>
                <div className="grid grid-cols-2 gap-y-6 gap-x-4">
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Customer</p>
                        <p className="text-sm text-gray-200 font-medium">{data.customer.name}</p>
                        <p className="text-sm text-gray-400">{data.customer.email}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Razorpay Payment ID</p>
                        <p className="text-sm text-gray-200 font-mono">{data.payment.razorpay_payment_id}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Failure Reason</p>
                        <p className="text-sm text-gray-200">{data.payment.failure_reason}</p>
                        <p className="text-xs text-red-400 font-mono mt-0.5">{data.payment.failure_code}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Recovered Amount</p>
                        <p className="text-sm font-medium text-emerald-400">{formatCurrency(data.case.recovered_amount, data.payment.currency)}</p>
                    </div>
                </div>
            </div>

            {/* AI Diagnosis Card */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                    <Cpu className="w-32 h-32" />
                </div>
                <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-purple-400" />
                    AI Diagnosis & Execution
                </h3>
                <div className="grid grid-cols-2 gap-6 relative z-10">
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Classification</p>
                        <p className="text-sm text-white font-medium">{data.case.reason || '—'}</p>
                    </div>
                    <div>
                        <p className="text-xs text-gray-500 mb-1">Confidence Score</p>
                        <p className="text-sm text-white font-medium">
                            {data.case.recovery_probability !== null ? `${(data.case.recovery_probability * 100).toFixed(0)}%` : '—'}
                        </p>
                    </div>
                    <div className="col-span-2">
                        <p className="text-xs text-gray-500 mb-1">Recommended Action</p>
                        <p className="text-sm text-purple-300 font-medium font-mono">{data.case.recommended_action || '—'}</p>
                    </div>
                    <div className="col-span-2">
                        <p className="text-xs text-gray-500 mb-1">Execution Action</p>
                        <div className="flex items-center gap-2">
                            <p className="text-sm text-blue-400 font-medium font-mono">{data.case.actual_action || '—'}</p>
                            {data.audit_logs.some(log => log.event_type === 'action_executed' && log.metadata_json?.is_simulated) && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-gray-800 text-gray-400 border border-gray-700">Simulated Demo</span>
                            )}
                            {data.audit_logs.some(log => log.event_type === 'action_executed' && log.metadata_json?.is_simulated === False) && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">Real Test Mode</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {/* Audit Timeline */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-white mb-6 uppercase tracking-wider text-gray-500">Audit Timeline</h3>
            <div className="relative border-l border-gray-800 ml-3 space-y-6">
                {data.audit_logs.map((log) => (
                    <div key={log.id} className="relative pl-6">
                        <div className="absolute -left-3 top-0 bg-gray-950 rounded-full p-0.5 border border-gray-800">
                            {getEventIcon(log.event_type, log.status)}
                        </div>
                        <div className="mb-1">
                            <span className="text-xs font-semibold text-white">{log.action}</span>
                        </div>
                        <div className="text-xs text-gray-500 mb-2">
                            {new Date(log.timestamp).toLocaleString()} • {log.actor}
                        </div>
                        {log.metadata_json && Object.keys(log.metadata_json).length > 0 && (
                            <div className="bg-gray-950 rounded border border-gray-800 p-2 text-[10px] font-mono text-gray-400 overflow-x-auto">
                                <pre>{JSON.stringify(log.metadata_json, null, 2)}</pre>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
      </div>
    </div>
  );
}
