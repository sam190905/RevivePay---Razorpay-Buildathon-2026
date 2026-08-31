# RevivePay API Documentation

This document describes the minimal API surface created for the RevivePay MVP.

## Base URL
All endpoints are relative to `http://localhost:8000` (or the deployed backend URL).

## Endpoints

### 1. Health Check
`GET /health`
Returns the status of the backend server.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

### 2. Dashboard Summary
`GET /api/dashboard/summary`
Retrieves aggregated metrics for the dashboard (Revenue at Risk, Recovered Revenue, Case counts, etc.).

**Response (200 OK):**
```json
{
  "metrics": {
    "revenue_at_risk": 480000,
    "revenue_recovered": 192000,
    "cases_processed": 10,
    "recovery_rate": 0.8
  },
  "recent_cases": [ ... ]
}
```

### 3. List Recovery Cases
`GET /api/recovery-cases`
Lists all recovery cases.

### 4. Get Case Detail
`GET /api/recovery-cases/{id}`
Retrieves a specific recovery case, including the payment context, customer details, and the full audit log timeline.

### 5. Demo Control: Trigger Scenario
`POST /api/demo/scenarios`
Fires a deterministic synthetic webhook payload to simulate specific recovery scenarios for testing and demonstration.

**Payload:**
```json
{
  "scenario": "successful_recovery"
}
```
*Valid scenarios: `successful_recovery`, `payment_link_recovery`, `blocked_recovery`, `failed_execution`, `duplicate_webhook`.*

### 6. Razorpay Webhook Receiver
`POST /webhooks/razorpay`
The core entrypoint for all Razorpay events.

**Headers Required:**
- `X-Razorpay-Signature`: HMAC SHA-256 signature.
- `X-Razorpay-Event-Id`: Unique event ID.

**Supported Events:**
- `payment.failed`: Triggers the AI diagnosis and recovery pipeline.
- `payment_link.paid`: Updates recovery metrics for successful automated interventions.
- `payment.captured`: Ignored for attribution (to prevent double-counting).

## Security & Idempotency
- All webhooks undergo signature verification using `RAZORPAY_WEBHOOK_SECRET`.
- A `WebhookEvent` table tracks `X-Razorpay-Event-Id` to guarantee that duplicate webhooks from Razorpay do not result in duplicated recovery cases or double-counted revenue.
