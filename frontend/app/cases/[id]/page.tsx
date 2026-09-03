"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchCaseDetail, CaseDetail, AuditLog, simulateCustomerPayment, syncPaymentStatus } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Badge } from "@/components/badge";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  Cpu,
  Shield,
  Zap,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Ban,
  CircleDot,
  Loader2,
  RefreshCw,
} from "lucide-react";

/* ── helpers ─────────────────────────────────────────────────────── */

function statusMeta(status: string) {
  const map: Record<string, { label: string; color: string; icon: React.ReactNode; description: string }> = {
    open: {
      label: "Open",
      color: "text-[var(--brand)]",
      icon: <CircleDot className="w-5 h-5 text-[var(--brand)]" />,
      description: "Case is open and awaiting processing.",
    },
    processing: {
      label: "Processing",
      color: "text-[var(--brand)]",
      icon: <Loader2 className="w-5 h-5 text-[var(--brand)] animate-spin" />,
      description: "Recovery action is being executed.",
    },
    recovered: {
      label: "Recovered",
      color: "text-[var(--success)]",
      icon: <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />,
      description: "Full amount has been successfully recovered.",
    },
    partially_recovered: {
      label: "Partially Recovered",
      color: "text-[var(--success)]",
      icon: <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />,
      description: "A portion of the amount has been recovered.",
    },
    failed: {
      label: "Failed",
      color: "text-[var(--danger)]",
      icon: <XCircle className="w-5 h-5 text-[var(--danger)]" />,
      description: "Recovery was unsuccessful.",
    },
    manual_review: {
      label: "Manual Review",
      color: "text-[var(--warning)]",
      icon: <Ban className="w-5 h-5 text-[var(--warning)]" />,
      description: "Case requires manual review by an operator.",
    },
  };
  return map[status] || { label: status, color: "text-[var(--text-muted)]", icon: <Clock className="w-5 h-5 text-[var(--text-muted)]" />, description: "" };
}

function eventTitle(eventType: string, log: AuditLog): string {
  switch (eventType) {
    case "case_created": return "Payment Failed — Case Created";
    case "ai_diagnosis":
      return log.actor === "system_fallback" ? "Diagnosis — Deterministic Fallback" : "Diagnosis — AI Analysis";
    case "policy_check": {
      const outcome = log.metadata_json?.outcome;
      if (outcome === "BLOCK" || outcome === "MANUAL_REVIEW") return "Policy — Blocked";
      return "Policy — Approved";
    }
    case "action_executed": {
      if (log.status === "failed") return "Execution — Failed";
      if (log.action?.includes("manual review")) return "Routed to Manual Review";
      return "Action Executed";
    }
    case "verification": return "Recovery Verified";
    default: return log.action || eventType;
  }
}

function eventDescription(log: AuditLog): string {
  const m = log.metadata_json;
  if (!m) return "";
  switch (log.event_type) {
    case "case_created":
      return `Webhook event received. Error code: ${m.error_code || "none"}.`;
    case "ai_diagnosis":
      return `Classified as "${m.classification}" with ${typeof m.confidence === "number" ? `${(m.confidence * 100).toFixed(0)}%` : "Not available"} confidence. Recommended action: ${m.recommended_action || "Not available"}.`;
    case "policy_check": {
      const parts = [`Outcome: ${m.outcome}`, `Risk: ${m.risk_level || "—"}`];
      if (m.reason) parts.push(m.reason);
      if (m.violated_rule) parts.push(`Violated: ${m.violated_rule}`);
      return parts.join(". ");
    }
    case "action_executed":
      if (log.status === "failed") return `Error: ${m.error || "Unknown error"}.`;
      if (m.provider_id) return `Payment Link created successfully.`;
      if (m.reason) return m.reason;
      return log.action || "";
    case "verification":
      return `Verified recovery of ${formatCurrency(m.recovered_amount, "INR")}. Status updated to ${m.new_status?.replace("_", " ")}.`;
    default:
      return log.action || "";
  }
}

function eventKeyValues(log: AuditLog): [string, string][] {
  const m = log.metadata_json;
  if (!m) return [];
  switch (log.event_type) {
    case "action_executed":
      if (m.provider_id) {
        const pairs: [string, string][] = [["Provider ID", m.provider_id]];
        if (m.result) pairs.push(["URL", m.result]);
        return pairs;
      }
      return [];
    default:
      return [];
  }
}

function getEventIcon(eventType: string, status: string, actor?: string) {
  if (status === "failed") return <XCircle className="w-5 h-5 text-[var(--danger)]" />;
  switch (eventType) {
    case "case_created": return <AlertCircle className="w-5 h-5 text-[var(--brand)]" />;
    case "ai_diagnosis":
      return actor === "system_fallback"
        ? <Cpu className="w-5 h-5 text-[var(--text-muted)]" />
        : <Cpu className="w-5 h-5 text-purple-500" />;
    case "policy_check": return <Shield className="w-5 h-5 text-[var(--warning)]" />;
    case "action_executed": return <Zap className="w-5 h-5 text-[var(--brand)]" />;
    case "verification": return <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />;
    default: return <Clock className="w-5 h-5 text-[var(--text-muted)]" />;
  }
}

/* ── collapsible raw json ────────────────────────────────────────── */

function RawDetails({ data }: { data: any }) {
  const [open, setOpen] = useState(false);
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
      >
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {open ? "Hide raw details" : "View raw details"}
      </button>
      {open && (
        <div className="mt-1.5 bg-[var(--surface-overlay)] rounded border border-[var(--border-subtle)] p-2.5 text-[10px] font-mono text-[var(--text-muted)] overflow-x-auto shadow-inner">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

/* ── section wrapper ─────────────────────────────────────────────── */

function Section({ title, icon, children, className = "" }: { title: string; icon?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-sm ${className}`}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-5 flex items-center gap-2">
        {icon}
        {title}
      </h3>
      {children}
    </div>
  );
}

/* ── main page ───────────────────────────────────────────────────── */

export default function CaseDetailPage() {
  const params = useParams();
  const [data, setData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [isSimulatingPayment, setIsSimulatingPayment] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  const loadData = () => {
    if (params.id) {
      fetchCaseDetail(params.id as string)
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    loadData();
  }, [params.id]);

  useEffect(() => {
    if (!data) return;
    const isProcessing = data.case.status === "open" || data.case.status === "processing";
    if (isProcessing) {
      const interval = setInterval(loadData, 2000);
      return () => clearInterval(interval);
    }
  }, [data?.case.status]);

  if (loading && !data)
    return (
      <div className="flex items-center gap-3 text-gray-400 animate-pulse py-16">
        <Loader2 className="w-5 h-5 animate-spin" /> Loading case details…
      </div>
    );
  if (!data) return <div className="text-red-400 py-16">Failed to load case.</div>;

  const sm = statusMeta(data.case.status);

  /* Extract structured data from audit logs */
  const aiLog = data.audit_logs.find((l) => l.event_type === "ai_diagnosis");
  const policyLog = data.audit_logs.find((l) => l.event_type === "policy_check");
  const execLog = data.audit_logs.find((l) => l.event_type === "action_executed" && l.actor === "action_executor");
  const verificationLog = data.audit_logs.find((l) => l.event_type === "verification");

  const isAISource = aiLog?.actor === "ai_agent";
  const isDeterministicFallback = aiLog?.actor === "system_fallback";

  const execMeta = execLog?.metadata_json;
  const hasPaymentLink = execMeta?.provider_id && data.case.actual_action === "create_payment_link";
  const paymentLinkUrl = execMeta?.result;
  const isSimulated = execMeta?.is_simulated === true;
  const isRealTestMode = execMeta?.is_simulated === false;

  const isRecovered = data.case.status === "recovered" || data.case.status === "partially_recovered";

  /* AI diagnosis metadata normalization */
  const aiMeta = aiLog?.metadata_json;
  const aiClassification = aiMeta?.classification;
  const aiConfidence = aiMeta?.confidence;
  const aiRecommendedAction = aiMeta?.recommended_action;
  const aiReason = aiMeta?.reason;

  const handleSimulatePayment = async () => {
    if (!data) return;
    try {
      setIsSimulatingPayment(true);
      await simulateCustomerPayment(data.case.id);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSimulatingPayment(false);
    }
  };

  const handleSyncPayment = async () => {
    if (!data) return;
    try {
      setIsSyncing(true);
      await syncPaymentStatus(data.case.id);
      loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="max-w-5xl">
      {/* Navigation */}
      <Link
        href="/cases"
        className="mb-6 inline-flex items-center text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Cases
      </Link>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            {sm.icon}
            <h1 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight">
              Case Details
            </h1>
            <Badge status={data.case.status} />
          </div>
          <p className="text-xs text-[var(--text-secondary)] font-mono ml-9">{data.case.id}</p>
          {sm.description && (
            <p className="text-sm text-[var(--text-muted)] mt-1.5 ml-9">{sm.description}</p>
          )}
        </div>

        {/* Amount at Risk callout */}
        <div className="sm:text-right flex-shrink-0 bg-[var(--surface)] border border-[var(--border-subtle)] p-4 rounded-xl shadow-sm">
          <p className="text-[10px] text-[var(--text-secondary)] uppercase tracking-widest font-semibold mb-1">Amount at Risk</p>
          <p className="text-3xl font-bold text-[var(--text-primary)] tabular-nums tracking-tight">
            {formatCurrency(data.case.amount_at_risk, data.payment.currency)}
          </p>
          {isRecovered && data.case.recovered_amount > 0 && (
            <p className="text-sm font-semibold text-[var(--success)] mt-1 tabular-nums">
              Recovered {formatCurrency(data.case.recovered_amount, data.payment.currency)}
            </p>
          )}
        </div>
      </div>

      {/* ── Progress Tracker ───────────────────────────────────── */}
      <div className="mb-8 p-6 bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold flex items-center gap-2 text-[var(--text-primary)]">
            {(data.case.status === "open" || data.case.status === "processing") && !(execLog || hasPaymentLink) ? (
              <><Loader2 className="w-4 h-4 animate-spin text-[var(--brand)]" /> AI Recovery in Progress</>
            ) : (data.case.status === "open" || data.case.status === "processing") && (execLog || hasPaymentLink) ? (
              <><Clock className="w-4 h-4 text-[var(--brand)]" /> Waiting for customer payment</>
            ) : data.case.status === "recovered" || data.case.status === "partially_recovered" ? (
              <><CheckCircle2 className="w-4 h-4 text-[var(--success)]" /> Revenue Recovered</>
            ) : data.case.status === "failed" ? (
               <><XCircle className="w-4 h-4 text-[var(--danger)]" /> Recovery Failed</>
            ) : data.case.status === "manual_review" ? (
               <><Ban className="w-4 h-4 text-[var(--warning)]" /> Manual Review Required</>
            ) : (
              "Recovery Status"
            )}
          </h4>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto text-xs pb-2 scrollbar-hide">
          {[
            { label: "Payment Failed", status: "completed" },
            { label: "Case Created", status: "completed" },
            { label: "AI Diagnosis", status: aiLog ? "completed" : ((data.case.status === "open" || data.case.status === "processing") ? "processing" : "pending") },
            { label: "Policy Check", status: policyLog ? "completed" : (aiLog && (data.case.status === "open" || data.case.status === "processing") ? "processing" : "pending") },
            { label: "Recovery Action", status: (execLog || hasPaymentLink) ? (execLog?.status === "failed" ? "failed" : "completed") : (policyLog && (data.case.status === "open" || data.case.status === "processing") ? "processing" : "pending") },
            { label: "Verification", status: verificationLog ? "completed" : ((execLog || hasPaymentLink) && data.case.status !== "failed" && data.case.status !== "manual_review" ? "processing" : "pending") }
          ].map((step, i, arr) => (
            <div key={i} className="flex items-center gap-2 flex-shrink-0">
              <div className={`flex items-center justify-center w-6 h-6 rounded-full border ${step.status === 'completed' ? 'bg-[var(--success)]/10 border-[var(--success)]/30 text-[var(--success)]' : step.status === 'processing' ? 'bg-[var(--brand)]/10 border-[var(--brand)]/30 text-[var(--brand)]' : step.status === 'failed' ? 'bg-[var(--danger)]/10 border-[var(--danger)]/30 text-[var(--danger)]' : 'bg-[var(--surface-overlay)] border-[var(--border-subtle)] text-[var(--text-muted)]'}`}>
                {step.status === 'completed' ? <CheckCircle2 className="w-4 h-4" /> : step.status === 'failed' ? <XCircle className="w-4 h-4" /> : step.status === 'processing' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CircleDot className="w-3 h-3" />}
              </div>
              <span className={`${step.status === 'completed' ? 'text-[var(--text-primary)]' : step.status === 'processing' ? 'text-[var(--brand)] font-semibold' : step.status === 'failed' ? 'text-[var(--danger)] font-semibold' : 'text-[var(--text-muted)]'}`}>
                {step.label}
              </span>
              {i < arr.length - 1 && <div className="w-8 h-px bg-[var(--border-subtle)] mx-2" />}
            </div>
          ))}
        </div>
      </div>

      {/* ── Recovery Outcome Banner ─────────────────────────────── */}
      {isRecovered && verificationLog && (
        <div className="mb-8 bg-[var(--success)]/10 border border-[var(--success)]/30 rounded-xl px-6 py-4 flex items-start gap-4">
          <CheckCircle2 className="w-6 h-6 text-[var(--success)] mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-[var(--success)]">
              {data.case.status === "recovered" ? "Fully Recovered" : "Partially Recovered"} — {formatCurrency(data.case.recovered_amount, data.payment.currency)}
            </p>
            <p className="text-xs text-[var(--text-primary)] mt-1 opacity-90">
              Recovery was verified after the payment link was paid. Revenue has been confirmed and attributed to this case.
            </p>
          </div>
        </div>
      )}

      {data.case.status === "failed" && (
        <div className="mb-8 bg-[var(--danger)]/10 border border-[var(--danger)]/30 rounded-xl px-6 py-4 flex items-start gap-4">
          <XCircle className="w-6 h-6 text-[var(--danger)] mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-[var(--danger)]">Recovery Failed</p>
            <p className="text-xs text-[var(--text-primary)] mt-1 opacity-90">
              The recovery action could not be completed. See the timeline below for details.
            </p>
          </div>
        </div>
      )}

      {data.case.status === "manual_review" && (
        <div className="mb-8 bg-[var(--warning)]/10 border border-[var(--warning)]/30 rounded-xl px-6 py-4 flex items-start gap-4">
          <Ban className="w-6 h-6 text-[var(--warning)] mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-[var(--warning)]">Requires Manual Review</p>
            <p className="text-xs text-[var(--text-primary)] mt-1 opacity-90">
              Policy engine blocked automatic recovery. This case needs manual review by an operator.
            </p>
          </div>
        </div>
      )}

      {/* ── Grid: Left (overview, AI, action) · Right (timeline) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">

          {/* ── Overview Card ──────────────────────────────────── */}
          <Section title="Overview">
            <div className="grid grid-cols-2 gap-x-6 gap-y-5">
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Customer</p>
                <p className="text-sm text-[var(--text-primary)] font-semibold">{data.customer.name}</p>
                {data.customer.email && (
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">{data.customer.email}</p>
                )}
                {data.customer.phone && (
                  <p className="text-xs text-[var(--text-muted)] mt-0.5">{data.customer.phone}</p>
                )}
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Razorpay Payment ID</p>
                <p className="text-sm text-[var(--text-primary)] font-mono">{data.payment.razorpay_payment_id}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Failure Reason</p>
                <p className="text-sm text-[var(--text-primary)]">{data.payment.failure_reason || "—"}</p>
                {data.payment.failure_code && (
                  <p className="text-xs text-[var(--danger)]/80 font-mono mt-0.5">{data.payment.failure_code}</p>
                )}
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Recovered Amount</p>
                <p className={`text-sm font-bold tabular-nums ${data.case.recovered_amount > 0 ? "text-[var(--success)]" : "text-[var(--text-muted)]"}`}>
                  {formatCurrency(data.case.recovered_amount, data.payment.currency)}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Opened</p>
                <p className="text-sm text-[var(--text-primary)]">{new Date(data.case.opened_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Payment Method</p>
                <p className="text-sm text-[var(--text-primary)] capitalize">{data.payment.status}</p>
              </div>
            </div>
          </Section>

          {/* ── AI Diagnosis Card ──────────────────────────────── */}
          <Section
            title="AI Diagnosis"
            icon={<Cpu className={`w-4 h-4 ${isAISource ? "text-purple-500" : "text-[var(--text-muted)]"}`} />}
          >
            {/* Decision source badge */}
            <div className="mb-5 flex items-center gap-2">
              {isAISource && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-purple-500/10 text-purple-500 border border-purple-500/20">
                  <Cpu className="w-3 h-3" /> AI / Gemini
                </span>
              )}
              {isDeterministicFallback && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[var(--surface-overlay)] text-[var(--text-secondary)] border border-[var(--border-subtle)]">
                  <Cpu className="w-3 h-3" /> Deterministic Fallback
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Classification</p>
                <p className="text-sm text-[var(--text-primary)] font-semibold">{aiClassification || data.case.reason || "Not available"}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Confidence</p>
                <div className="flex items-center gap-2">
                  <p className="text-sm text-[var(--text-primary)] font-bold tabular-nums">
                    {typeof aiConfidence === "number" ? `${(aiConfidence * 100).toFixed(0)}%` : "Not available"}
                  </p>
                  {typeof aiConfidence === "number" && (
                    <div className="flex-1 max-w-[80px] h-1.5 bg-[var(--border-subtle)] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-purple-500"
                        style={{ width: `${Math.min(aiConfidence * 100, 100)}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Recommended Action</p>
                <p className="text-sm text-purple-500 font-bold font-mono">{aiRecommendedAction || "Not available"}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Decision Source</p>
                <p className="text-sm text-[var(--text-primary)]">
                  {isAISource ? "Gemini" : isDeterministicFallback ? "Rule-based engine" : "—"}
                </p>
              </div>
            </div>

            {/* Policy outcome */}
            {policyLog && (
              <div className="mt-5 pt-5 border-t border-[var(--border-subtle)]">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-4 h-4 text-[var(--warning)]" />
                  <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider font-bold">Policy Decision</p>
                </div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-3">
                  <div>
                    <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Outcome</p>
                    <p className={`text-sm font-bold ${policyLog.metadata_json?.outcome === "APPROVE" ? "text-[var(--success)]" : "text-[var(--warning)]"}`}>
                      {policyLog.metadata_json?.outcome || "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Risk Level</p>
                    <p className="text-sm text-[var(--text-primary)] font-medium">{policyLog.metadata_json?.risk_level || "—"}</p>
                  </div>
                  {policyLog.metadata_json?.reason && (
                    <div className="col-span-2">
                      <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Reason</p>
                      <p className="text-sm text-[var(--text-primary)]">{policyLog.metadata_json.reason}</p>
                    </div>
                  )}
                  {policyLog.metadata_json?.violated_rule && (
                    <div className="col-span-2">
                      <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Violated Rule</p>
                      <p className="text-sm text-[var(--danger)] font-mono font-bold">{policyLog.metadata_json.violated_rule}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <RawDetails data={aiLog?.metadata_json} />
          </Section>

          {/* ── Recovery Action Card (only if action was taken) ── */}
          {(execLog || hasPaymentLink) && (
            <Section
              title="Recovery Action"
              icon={<Zap className="w-4 h-4 text-[var(--brand)]" />}
            >
              <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Action</p>
                  <p className="text-sm text-[var(--brand)] font-bold font-mono">
                    {data.case.actual_action?.toUpperCase() || "—"}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Execution Status</p>
                  <div className="flex items-center gap-2">
                    {execLog?.status === "success" ? (
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                    ) : (
                      <XCircle className="w-4 h-4 text-[var(--danger)]" />
                    )}
                    <p className={`text-sm font-bold ${execLog?.status === "success" ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
                      {execLog?.status === "success" ? "Success" : "Failed"}
                    </p>
                  </div>
                </div>

                {/* Mode badge */}
                <div>
                  <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Mode</p>
                  {isSimulated && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[var(--surface-overlay)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
                      Simulated Demo
                    </span>
                  )}
                  {isRealTestMode && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[var(--brand)]/10 text-[var(--brand)] border border-[var(--brand)]/20">
                      Real Test Mode
                    </span>
                  )}
                  {!isSimulated && !isRealTestMode && (
                    <span className="text-sm text-[var(--text-muted)]">—</span>
                  )}
                </div>

                {/* Recovered amount */}
                <div>
                  <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Recovered Amount</p>
                  <p className={`text-sm font-bold tabular-nums ${data.case.recovered_amount > 0 ? "text-[var(--success)]" : "text-[var(--text-muted)]"}`}>
                    {formatCurrency(data.case.recovered_amount, data.payment.currency)}
                  </p>
                </div>

                {/* Payment Link details */}
                {hasPaymentLink && (
                  <>
                    <div className="col-span-2 border-t border-[var(--border-subtle)] pt-4 mt-1">
                      <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-2">Payment Link Details</p>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-[var(--text-secondary)] w-20 flex-shrink-0">Provider ID</span>
                          <span className="text-xs text-[var(--text-primary)] font-mono">{execMeta.provider_id}</span>
                        </div>
                        {isSimulated && (
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] text-[var(--text-secondary)] w-20 flex-shrink-0">Mode</span>
                            <span className="text-xs text-[var(--warning)] font-semibold">Simulated Demo</span>
                          </div>
                        )}
                        {!isRecovered && isSimulated && (
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] text-[var(--text-secondary)] w-20 flex-shrink-0">Status</span>
                            <span className="text-xs text-[var(--brand)] font-semibold animate-pulse">Waiting for customer payment</span>
                          </div>
                        )}
                        {!isSimulated && paymentLinkUrl && (
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] text-[var(--text-secondary)] w-20 flex-shrink-0">URL</span>
                            <span className="text-xs text-[var(--text-primary)] font-mono truncate">{paymentLinkUrl}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {!isRecovered && isSimulated && (
                      <div className="col-span-2">
                        <button
                          onClick={handleSimulatePayment}
                          disabled={isSimulatingPayment}
                          className="flex items-center gap-2 px-4 py-2 bg-[var(--warning)]/10 text-[var(--warning)] hover:bg-[var(--warning)]/20 rounded-lg text-sm font-semibold transition-colors border border-[var(--warning)]/20 disabled:opacity-50"
                        >
                          {isSimulatingPayment ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-4 h-4" />
                          )}
                          {isSimulatingPayment ? "Simulating..." : "Simulate Customer Payment"}
                        </button>
                      </div>
                    )}

                    {!isSimulated && paymentLinkUrl && (
                      <div className="col-span-2 flex items-center gap-3">
                        <a
                          href={paymentLinkUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-[var(--brand)]/10 text-[var(--brand)] border border-[var(--brand)]/20 hover:bg-[var(--brand)]/20 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Open Payment Link
                        </a>
                        {!isRecovered && (
                          <button
                            onClick={handleSyncPayment}
                            disabled={isSyncing}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-[var(--surface-overlay)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:bg-[var(--border-subtle)] transition-colors disabled:opacity-50"
                          >
                            <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
                            {isSyncing ? "Syncing..." : "Sync Payment Status"}
                          </button>
                        )}
                      </div>
                    )}
                  </>
                )}

                {/* Execution error */}
                {execLog?.status === "failed" && execMeta?.error && (
                  <div className="col-span-2 mt-1">
                    <p className="text-[11px] text-[var(--text-secondary)] uppercase tracking-wider mb-1">Error</p>
                    <p className="text-sm text-[var(--danger)] font-mono break-all">{execMeta.error}</p>
                  </div>
                )}
              </div>
            </Section>
          )}
        </div>

        {/* ── Audit Timeline (right column) ─────────────────────── */}
        <div>
          <Section title="Audit Timeline" className="sticky top-24">
            <div className="relative border-l border-[var(--border-subtle)] ml-2.5 space-y-6">
              {data.audit_logs.map((log) => {
                const kvs = eventKeyValues(log);
                return (
                  <div key={log.id} className="relative pl-6">
                    {/* icon dot */}
                    <div className="absolute -left-[14px] top-0 bg-[var(--surface)] rounded-full p-0.5 border border-[var(--border-subtle)]">
                      {getEventIcon(log.event_type, log.status, log.actor)}
                    </div>

                    {/* title */}
                    <p className="text-sm font-bold text-[var(--text-primary)] leading-tight">
                      {eventTitle(log.event_type, log)}
                    </p>

                    {/* time + actor */}
                    <p className="text-[11px] text-[var(--text-secondary)] mt-1 font-medium">
                      {new Date(log.timestamp).toLocaleString()}
                      <span className="mx-1.5">·</span>
                      <span className="text-[var(--text-muted)]">{log.actor === "system_fallback" ? "deterministic engine" : log.actor}</span>
                    </p>

                    {/* description */}
                    <p className="text-xs text-[var(--text-secondary)] mt-2 leading-relaxed">
                      {eventDescription(log)}
                    </p>

                    {/* inline key-values */}
                    {kvs.length > 0 && (
                      <div className="mt-3 space-y-1 bg-[var(--surface-overlay)] p-2.5 rounded-lg border border-[var(--border-subtle)] shadow-inner">
                        {kvs.map(([k, v]) => (
                          <div key={k} className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 text-[11px]">
                            <span className="text-[var(--text-muted)] font-medium uppercase tracking-wider w-20 flex-shrink-0">{k}</span>
                            <span className="text-[var(--text-primary)] font-mono truncate font-semibold">{v}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* collapsible raw */}
                    <RawDetails data={log.metadata_json} />
                  </div>
                );
              })}
            </div>
          </Section>
        </div>
      </div>
    </div>
  );
}
