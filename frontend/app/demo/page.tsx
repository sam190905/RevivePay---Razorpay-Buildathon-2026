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
      icon: <CheckCircle2 className="w-6 h-6 text-emerald-400" />,
      color: "hover:border-emerald-500/50"
    },
    {
      id: "payment_link_recovery",
      name: "Payment Link Recovery",
      description: "Triggers an INSUFFICIENT_FUNDS failure. The AI recommends a payment link, which is generated, and the simulated customer completes the payment.",
      icon: <CheckCircle2 className="w-6 h-6 text-emerald-400" />,
      color: "hover:border-emerald-500/50"
    },
    {
      id: "blocked_recovery",
      name: "Guardrail Block (Fraud)",
      description: "Triggers a high-value FRAUD failure. The Policy Engine firmly blocks automated actions and routes to Manual Review. Revenue remains 0.",
      icon: <ShieldAlert className="w-6 h-6 text-amber-400" />,
      color: "hover:border-amber-500/50"
    },
    {
      id: "duplicate_webhook",
      name: "Duplicate Webhook",
      description: "Sends the exact same webhook event twice in rapid succession. The system's idempotency ensures only one case is created.",
      icon: <CheckCircle2 className="w-6 h-6 text-blue-400" />,
      color: "hover:border-blue-500/50"
    },
    {
      id: "failed_execution",
      name: "Execution Failure",
      description: "Simulates an upstream API timeout during action execution. The engine catches the error, logs it to audit trail, and marks the action as failed.",
      icon: <XCircle className="w-6 h-6 text-red-400" />,
      color: "hover:border-red-500/50"
    }
  ];

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">Demo Scenarios</h1>
        <p className="mt-1 text-sm text-gray-400">
          Trigger deterministic, end-to-end scenarios to demonstrate the AI Recovery Engine and Guardrails.
        </p>
      </div>

      {result && (
        <div className={`mb-6 p-4 rounded-lg border text-sm ${result.status === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
          {result.message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {scenarios.map((s) => (
          <div key={s.id} className={`bg-gray-900 border border-gray-800 rounded-xl p-6 transition-colors ${s.color}`}>
            <div className="flex items-start gap-4">
              <div className="mt-1 bg-gray-950 p-2 rounded-lg border border-gray-800 shrink-0">
                {s.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-1">{s.name}</h3>
                <p className="text-sm text-gray-400 leading-relaxed mb-4">{s.description}</p>
                <button
                  onClick={() => handleTrigger(s.id)}
                  disabled={loading !== null}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading === s.id ? (
                    <span className="animate-pulse">Running...</span>
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
