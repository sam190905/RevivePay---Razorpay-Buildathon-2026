"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchCaseDetail, CaseDetail, AuditLog } from "@/lib/api";
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
} from "lucide-react";

/* ── helpers ─────────────────────────────────────────────────────── */

function statusMeta(status: string) {
  const map: Record<string, { label: string; color: string; icon: React.ReactNode; description: string }> = {
    open: {
      label: "Open",
      color: "text-blue-400",
      icon: <CircleDot className="w-5 h-5 text-blue-400" />,
      description: "Case is open and awaiting processing.",
    },
    processing: {
      label: "Processing",
      color: "text-sky-400",
      icon: <Loader2 className="w-5 h-5 text-sky-400 animate-spin" />,
      description: "Recovery action is being executed.",
    },
    recovered: {
      label: "Recovered",
      color: "text-emerald-400",
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
      description: "Full amount has been successfully recovered.",
    },
    partially_recovered: {
      label: "Partially Recovered",
      color: "text-lime-400",
      icon: <CheckCircle2 className="w-5 h-5 text-lime-400" />,
      description: "A portion of the amount has been recovered.",
    },
    failed: {
      label: "Failed",
      color: "text-red-400",
      icon: <XCircle className="w-5 h-5 text-red-400" />,
      description: "Recovery was unsuccessful.",
    },
    manual_review: {
      label: "Manual Review",
      color: "text-amber-400",
      icon: <Ban className="w-5 h-5 text-amber-400" />,
      description: "Case requires manual review by an operator.",
    },
  };
  return map[status] || { label: status, color: "text-gray-400", icon: <Clock className="w-5 h-5 text-gray-400" />, description: "" };
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
  if (status === "failed") return <XCircle className="w-5 h-5 text-red-400" />;
  switch (eventType) {
    case "case_created": return <AlertCircle className="w-5 h-5 text-blue-400" />;
    case "ai_diagnosis":
      return actor === "system_fallback"
        ? <Cpu className="w-5 h-5 text-gray-400" />
        : <Cpu className="w-5 h-5 text-purple-400" />;
    case "policy_check": return <Shield className="w-5 h-5 text-amber-400" />;
    case "action_executed": return <Zap className="w-5 h-5 text-blue-400" />;
    case "verification": return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
    default: return <Clock className="w-5 h-5 text-gray-400" />;
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
        className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-300 transition-colors"
      >
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {open ? "Hide raw details" : "View raw details"}
      </button>
      {open && (
        <div className="mt-1.5 bg-gray-950 rounded border border-gray-800 p-2.5 text-[10px] font-mono text-gray-500 overflow-x-auto">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

/* ── section wrapper ─────────────────────────────────────────────── */

function Section({ title, icon, children, className = "" }: { title: string; icon?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-6 ${className}`}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-5 flex items-center gap-2">
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

  useEffect(() => {
    if (params.id) {
      fetchCaseDetail(params.id as string)
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading)
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

  return (
    <div className="max-w-5xl">
      {/* Navigation */}
      <Link
        href="/cases"
        className="mb-6 inline-flex items-center text-sm text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Cases
      </Link>

      {/* ── Header ──────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-1">
            {sm.icon}
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Case Details
            </h1>
            <Badge status={data.case.status} />
          </div>
          <p className="text-xs text-gray-500 font-mono ml-8">{data.case.id}</p>
          {sm.description && (
            <p className="text-sm text-gray-400 mt-1.5 ml-8">{sm.description}</p>
          )}
        </div>

        {/* Amount at Risk callout */}
        <div className="sm:text-right flex-shrink-0">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-1">Amount at Risk</p>
          <p className="text-2xl font-semibold text-white tabular-nums">
            {formatCurrency(data.case.amount_at_risk, data.payment.currency)}
          </p>
          {isRecovered && data.case.recovered_amount > 0 && (
            <p className="text-sm font-medium text-emerald-400 mt-1 tabular-nums">
              Recovered {formatCurrency(data.case.recovered_amount, data.payment.currency)}
            </p>
          )}
        </div>
      </div>

      {/* ── Recovery Outcome Banner ─────────────────────────────── */}
      {isRecovered && verificationLog && (
        <div className="mb-8 bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-6 py-4 flex items-start gap-4">
          <CheckCircle2 className="w-6 h-6 text-emerald-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-emerald-300">
              {data.case.status === "recovered" ? "Fully Recovered" : "Partially Recovered"} — {formatCurrency(data.case.recovered_amount, data.payment.currency)}
            </p>
            <p className="text-xs text-emerald-400/70 mt-1">
              Recovery was verified after the payment link was paid. Revenue has been confirmed and attributed to this case.
            </p>
          </div>
        </div>
      )}

      {data.case.status === "failed" && (
        <div className="mb-8 bg-red-500/5 border border-red-500/20 rounded-xl px-6 py-4 flex items-start gap-4">
          <XCircle className="w-6 h-6 text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-300">Recovery Failed</p>
            <p className="text-xs text-red-400/70 mt-1">
              The recovery action could not be completed. See the timeline below for details.
            </p>
          </div>
        </div>
      )}

      {data.case.status === "manual_review" && (
        <div className="mb-8 bg-amber-500/5 border border-amber-500/20 rounded-xl px-6 py-4 flex items-start gap-4">
          <Ban className="w-6 h-6 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-300">Requires Manual Review</p>
            <p className="text-xs text-amber-400/70 mt-1">
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
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Customer</p>
                <p className="text-sm text-gray-200 font-medium">{data.customer.name}</p>
                {data.customer.email && (
                  <p className="text-xs text-gray-400 mt-0.5">{data.customer.email}</p>
                )}
                {data.customer.phone && (
                  <p className="text-xs text-gray-400 mt-0.5">{data.customer.phone}</p>
                )}
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Razorpay Payment ID</p>
                <p className="text-sm text-gray-200 font-mono">{data.payment.razorpay_payment_id}</p>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Failure Reason</p>
                <p className="text-sm text-gray-200">{data.payment.failure_reason || "—"}</p>
                {data.payment.failure_code && (
                  <p className="text-xs text-red-400/70 font-mono mt-0.5">{data.payment.failure_code}</p>
                )}
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Recovered Amount</p>
                <p className={`text-sm font-medium tabular-nums ${data.case.recovered_amount > 0 ? "text-emerald-400" : "text-gray-400"}`}>
                  {formatCurrency(data.case.recovered_amount, data.payment.currency)}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Opened</p>
                <p className="text-sm text-gray-200">{new Date(data.case.opened_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Payment Method</p>
                <p className="text-sm text-gray-200 capitalize">{data.payment.status}</p>
              </div>
            </div>
          </Section>

          {/* ── AI Diagnosis Card ──────────────────────────────── */}
          <Section
            title="AI Diagnosis"
            icon={<Cpu className={`w-4 h-4 ${isAISource ? "text-purple-400" : "text-gray-500"}`} />}
          >
            {/* Decision source badge */}
            <div className="mb-5 flex items-center gap-2">
              {isAISource && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Cpu className="w-3 h-3" /> AI / OpenAI
                </span>
              )}
              {isDeterministicFallback && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-gray-500/10 text-gray-400 border border-gray-500/20">
                  <Cpu className="w-3 h-3" /> Deterministic Fallback
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-4">
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Classification</p>
                <p className="text-sm text-white font-medium">{aiClassification || data.case.reason || "Not available"}</p>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Confidence</p>
                <div className="flex items-center gap-2">
                  <p className="text-sm text-white font-medium tabular-nums">
                    {typeof aiConfidence === "number" ? `${(aiConfidence * 100).toFixed(0)}%` : "Not available"}
                  </p>
                  {typeof aiConfidence === "number" && (
                    <div className="flex-1 max-w-[80px] h-1.5 bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-purple-400/60"
                        style={{ width: `${Math.min(aiConfidence * 100, 100)}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Recommended Action</p>
                <p className="text-sm text-purple-300 font-medium font-mono">{aiRecommendedAction || "Not available"}</p>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Decision Source</p>
                <p className="text-sm text-gray-300">
                  {isAISource ? "OpenAI GPT" : isDeterministicFallback ? "Rule-based engine" : "—"}
                </p>
              </div>
            </div>

            {/* Policy outcome */}
            {policyLog && (
              <div className="mt-5 pt-5 border-t border-gray-800">
                <div className="flex items-center gap-2 mb-3">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <p className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold">Policy Decision</p>
                </div>
                <div className="grid grid-cols-2 gap-x-6 gap-y-3">
                  <div>
                    <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Outcome</p>
                    <p className={`text-sm font-semibold ${policyLog.metadata_json?.outcome === "APPROVE" ? "text-emerald-400" : "text-amber-400"}`}>
                      {policyLog.metadata_json?.outcome || "—"}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Risk Level</p>
                    <p className="text-sm text-gray-300">{policyLog.metadata_json?.risk_level || "—"}</p>
                  </div>
                  {policyLog.metadata_json?.reason && (
                    <div className="col-span-2">
                      <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Reason</p>
                      <p className="text-sm text-gray-300">{policyLog.metadata_json.reason}</p>
                    </div>
                  )}
                  {policyLog.metadata_json?.violated_rule && (
                    <div className="col-span-2">
                      <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Violated Rule</p>
                      <p className="text-sm text-red-400 font-mono">{policyLog.metadata_json.violated_rule}</p>
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
              icon={<Zap className="w-4 h-4 text-blue-400" />}
            >
              <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Action</p>
                  <p className="text-sm text-blue-400 font-medium font-mono">
                    {data.case.actual_action?.toUpperCase() || "—"}
                  </p>
                </div>
                <div>
                  <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Execution Status</p>
                  <div className="flex items-center gap-2">
                    {execLog?.status === "success" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400" />
                    )}
                    <p className={`text-sm font-medium ${execLog?.status === "success" ? "text-emerald-400" : "text-red-400"}`}>
                      {execLog?.status === "success" ? "Success" : "Failed"}
                    </p>
                  </div>
                </div>

                {/* Mode badge */}
                <div>
                  <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Mode</p>
                  {isSimulated && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-gray-800 text-gray-400 border border-gray-700">
                      Simulated Demo
                    </span>
                  )}
                  {isRealTestMode && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      Real Test Mode
                    </span>
                  )}
                  {!isSimulated && !isRealTestMode && (
                    <span className="text-sm text-gray-400">—</span>
                  )}
                </div>

                {/* Recovered amount */}
                <div>
                  <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Recovered Amount</p>
                  <p className={`text-sm font-medium tabular-nums ${data.case.recovered_amount > 0 ? "text-emerald-400" : "text-gray-400"}`}>
                    {formatCurrency(data.case.recovered_amount, data.payment.currency)}
                  </p>
                </div>

                {/* Payment Link details */}
                {hasPaymentLink && (
                  <>
                    <div className="col-span-2 border-t border-gray-800 pt-4 mt-1">
                      <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-2">Payment Link Details</p>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-gray-500 w-20 flex-shrink-0">Provider ID</span>
                          <span className="text-xs text-gray-300 font-mono">{execMeta.provider_id}</span>
                        </div>
                        {paymentLinkUrl && (
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] text-gray-500 w-20 flex-shrink-0">URL</span>
                            <span className="text-xs text-gray-300 font-mono truncate">{paymentLinkUrl}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    {paymentLinkUrl && (
                      <div className="col-span-2">
                        <a
                          href={paymentLinkUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Open Payment Link
                        </a>
                      </div>
                    )}
                  </>
                )}

                {/* Execution error */}
                {execLog?.status === "failed" && execMeta?.error && (
                  <div className="col-span-2 mt-1">
                    <p className="text-[11px] text-gray-500 uppercase tracking-wider mb-1">Error</p>
                    <p className="text-sm text-red-400 font-mono break-all">{execMeta.error}</p>
                  </div>
                )}
              </div>
            </Section>
          )}
        </div>

        {/* ── Audit Timeline (right column) ─────────────────────── */}
        <div>
          <Section title="Audit Timeline" className="sticky top-6">
            <div className="relative border-l border-gray-800 ml-2.5 space-y-5">
              {data.audit_logs.map((log) => {
                const kvs = eventKeyValues(log);
                return (
                  <div key={log.id} className="relative pl-6">
                    {/* icon dot */}
                    <div className="absolute -left-[13px] top-0 bg-gray-900 rounded-full p-0.5 border border-gray-800">
                      {getEventIcon(log.event_type, log.status, log.actor)}
                    </div>

                    {/* title */}
                    <p className="text-[13px] font-semibold text-gray-200 leading-tight">
                      {eventTitle(log.event_type, log)}
                    </p>

                    {/* time + actor */}
                    <p className="text-[11px] text-gray-500 mt-0.5">
                      {new Date(log.timestamp).toLocaleString()}
                      <span className="mx-1.5">·</span>
                      <span className="text-gray-500">{log.actor === "system_fallback" ? "deterministic engine" : log.actor}</span>
                    </p>

                    {/* description */}
                    <p className="text-xs text-gray-400 mt-1.5 leading-relaxed">
                      {eventDescription(log)}
                    </p>

                    {/* inline key-values */}
                    {kvs.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {kvs.map(([k, v]) => (
                          <div key={k} className="flex items-center gap-2 text-[11px]">
                            <span className="text-gray-500">{k}:</span>
                            <span className="text-gray-300 font-mono truncate">{v}</span>
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
