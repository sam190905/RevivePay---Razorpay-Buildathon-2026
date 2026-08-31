import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export interface MetricData {
  revenueAtRisk: number;
  recoverableRevenue: number;
  recoveryAttempted: number;
  revenueRecovered: number;
  recoveryRate: number;
  casesProcessed: number;
}

export interface FunnelData {
  name: string;
  value: number;
}

export interface ActionData {
  action: string;
  count: number;
}

export interface DashboardSummary {
  metrics: MetricData;
  funnel: FunnelData[];
  actions: ActionData[];
}

export interface RecoveryCase {
  id: string;
  customer_name: string;
  customer_email: string;
  amount: number;
  currency: string;
  failure_reason: string;
  recovery_probability: number | null;
  recommended_action: string | null;
  actual_action: string | null;
  status: string;
  opened_at: string;
  recovered_amount: number;
}

export interface AuditLog {
  id: string;
  event_type: string;
  actor: string;
  action: string;
  status: string;
  metadata_json: any;
  timestamp: string;
}

export interface CaseDetail {
  case: {
    id: string;
    amount_at_risk: number;
    reason: string | null;
    recovery_probability: number | null;
    status: string;
    recommended_action: string | null;
    actual_action: string | null;
    recovered_amount: number;
    opened_at: string;
    closed_at: string | null;
  };
  customer: {
    id: string;
    name: string;
    email: string;
    phone: string | null;
  };
  payment: {
    id: string;
    razorpay_payment_id: string;
    amount: number;
    currency: string;
    status: string;
    failure_code: string | null;
    failure_reason: string | null;
  };
  audit_logs: AuditLog[];
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const res = await api.get<DashboardSummary>("/dashboard/summary");
  return res.data;
}

export async function fetchRecoveryCases(): Promise<RecoveryCase[]> {
  const res = await api.get<RecoveryCase[]>("/recovery-cases");
  return res.data;
}

export async function fetchCaseDetail(id: string): Promise<CaseDetail> {
  const res = await api.get<CaseDetail>(`/recovery-cases/${id}`);
  return res.data;
}

export async function triggerDemoScenario(scenario: string): Promise<any> {
  const res = await api.post("/demo/scenarios", { scenario });
  return res.data;
}

export async function simulateCustomerPayment(caseId: string): Promise<any> {
  const res = await api.post("/demo/scenarios/simulate-payment", { case_id: caseId });
  return res.data;
}

export async function syncPaymentStatus(caseId: string): Promise<any> {
  const res = await api.post(`/recovery-cases/${caseId}/sync`);
  return res.data;
}
