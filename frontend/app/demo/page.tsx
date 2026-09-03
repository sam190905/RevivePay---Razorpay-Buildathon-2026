"use client";

import { useState } from "react";
import { triggerDemoScenario } from "@/lib/api";
import { Play, ShieldAlert, XCircle, CheckCircle2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function DemoPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [result, setResult] = useState<{status: string, message: string} | null>(null);
  const router = useRouter();

  const handleTrigger = async (scenario: string) => {
    setLoading(scenario);
    setResult(null);
    try {
      const res = await triggerDemoScenario(scenario);
      setResult({ status: 'success', message: `Scenario triggered successfully. Payment ID: ${res.payment_id}` });
      // Give the backend a second to process the webhook and then navigate
      setTimeout(() => {
        router.push('/cases');
      }, 1500);
    } catch (e: any) {
      setResult({ status: 'error', message: e.message || 'Failed to trigger scenario' });
    } finally {
      setLoading(null);
    }
  };

  const scenarios = [
    {
      id: "successful_recovery",
      name: "Successful Recovery",
      description: "Triggers a GATEWAY_ERROR which the AI will classify as a temporary failure. The policy engine will approve a Payment Link creation, and the customer successfully pays the link.",
      icon: <CheckCircle2 className="w-6 h-6 text-[var(--success)]" />,
      color: "hover:border-[var(--success)]/50"
    },
    {
      id: "payment_link_recovery",
      name: "Payment Link Recovery",
      description: "Triggers an INSUFFICIENT_FUNDS failure. The AI recommends a payment link, which is generated, and the simulated customer completes the payment.",
      icon: <CheckCircle2 className="w-6 h-6 text-[var(--success)]" />,
      color: "hover:border-[var(--success)]/50"
    },
    {
      id: "blocked_recovery",
      name: "Guardrail Block (Fraud)",
      description: "Triggers a high-value FRAUD failure. The Policy Engine firmly blocks automated actions and routes to Manual Review. Revenue remains 0.",
      icon: <ShieldAlert className="w-6 h-6 text-[var(--warning)]" />,
      color: "hover:border-[var(--warning)]/50"
    },
    {
      id: "duplicate_webhook",
      name: "Duplicate Webhook",
      description: "Sends the exact same webhook event twice in rapid succession. The system's idempotency ensures only one case is created.",
      icon: <CheckCircle2 className="w-6 h-6 text-[var(--brand)]" />,
      color: "hover:border-[var(--brand)]/50"
    },
    {
      id: "failed_execution",
      name: "Execution Failure",
      description: "Simulates an upstream API timeout during action execution. The engine catches the error, logs it to audit trail, and marks the action as failed.",
      icon: <XCircle className="w-6 h-6 text-[var(--danger)]" />,
      color: "hover:border-[var(--danger)]/50"
    }
  ];

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] tracking-tight">Demo Scenarios</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Trigger deterministic, end-to-end scenarios to demonstrate the AI Recovery Engine and Guardrails.
        </p>
      </div>

      {result && (
        <div className={`mb-6 p-4 rounded-xl border text-sm font-semibold shadow-sm ${result.status === 'success' ? 'bg-[var(--success)]/10 border-[var(--success)]/20 text-[var(--success)]' : 'bg-[var(--danger)]/10 border-[var(--danger)]/20 text-[var(--danger)]'}`}>
          {result.message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {scenarios.map((s) => (
          <div key={s.id} className={`bg-[var(--surface)] border border-[var(--border-subtle)] rounded-2xl p-6 transition-colors shadow-sm ${s.color}`}>
            <div className="flex items-start gap-4">
              <div className="mt-1 bg-[var(--surface-overlay)] p-2 rounded-xl border border-[var(--border-subtle)] shrink-0 shadow-inner">
                {s.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-[var(--text-primary)] mb-1">{s.name}</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-5">{s.description}</p>
                <button
                  onClick={() => handleTrigger(s.id)}
                  disabled={loading !== null}
                  className="flex items-center gap-2 bg-[var(--brand)] hover:bg-[var(--brand-dark)] text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors disabled:opacity-50 shadow-sm"
                >
                  {loading === s.id ? (
                    <span className="animate-pulse flex items-center gap-2"><div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"/> Running...</span>
                  ) : (
                    <>
                      <Play className="w-4 h-4" /> Trigger Scenario
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
