# RevivePay — Demo Script

Follow this script to demonstrate the five core scenarios of RevivePay.

## Prerequisites
1. Ensure the Backend (`uvicorn`) and Frontend (`npm run dev`) are running.
2. Ensure PostgreSQL is running.
3. Open the Dashboard at `http://localhost:3000`.

---

## Scenario 1: Payment Link Recovery (Happy Path)

**Goal:** Show how RevivePay detects a failed payment, diagnoses it, and automatically generates a payment link to recover the funds.

1. Navigate to the **Demo Control** page in the UI (or trigger `POST /api/demo/scenarios` with `"scenario": "payment_link_recovery"`).
2. The UI will simulate a `payment.failed` webhook (reason: Insufficient Funds).
3. **Wait 4 seconds**. The backend is automatically generating a Payment Link via Razorpay Test Mode and sending a simulated `payment_link.paid` webhook.
4. Navigate to **Recovery Cases** and click the newest case.
5. **Point out:**
   - **AI Diagnosis:** The model identified the reason and recommended a Payment Link.
   - **Policy Decision:** The deterministic engine approved the action.
   - **Recovery Action:** The Payment Link was successfully created (show the generated Provider ID / URL).
   - **Timeline:** Show how the `payment_link.paid` event was received and the case status transitioned to **Recovered**.

## Scenario 2: Successful Recovery (Direct)

**Goal:** Similar to the above, demonstrating a standard temporary gateway failure.

1. Trigger the `"successful_recovery"` scenario.
2. Open the newly generated case.
3. **Point out:** The failure was classified as a Gateway Error. The action was approved, executed, and the revenue was successfully recovered.

## Scenario 3: Guardrail Block (Manual Review)

**Goal:** Demonstrate the deterministic policy engine blocking the AI.

1. Trigger the `"blocked_recovery"` scenario.
2. Open the newly generated case.
3. **Point out:** 
   - The failure was flagged as "Suspected Fraud" and the amount was exceptionally high.
   - The Policy Engine returned a **BLOCK** / **MANUAL_REVIEW** decision.
   - **Crucially:** No automated action was taken, proving that the LLM cannot override the deterministic financial guardrails. The recovered amount remains ₹0.

## Scenario 4: Execution Failure

**Goal:** Demonstrate robust error handling when the Razorpay API fails.

1. Trigger the `"failed_execution"` scenario.
2. Open the case.
3. **Point out:**
   - The AI diagnosed the failure and the Policy Engine approved the action.
   - However, the Razorpay Action Executor encountered an error (simulated via a specific failure payload).
   - The `AuditLog` cleanly captures this failure, marking the case as **Failed**. No false success or revenue is reported.

## Scenario 5: Duplicate Webhook Protection

**Goal:** Demonstrate idempotency and data integrity.

1. Trigger the `"duplicate_webhook"` scenario.
2. This scenario instantly fires two identical `payment.failed` webhooks sequentially.
3. Navigate to **Recovery Cases**.
4. **Point out:** Only **one** case was created. The second webhook was caught by the idempotency check, preventing duplicate cases, duplicate AI calls, and duplicate actions.

---

## Final Talking Points
> *"RevivePay doesn't just use AI to guess why a payment failed. It combines AI-driven insights with strict, deterministic guardrails, securely executes actions through Razorpay, and tracks every step in an immutable audit log. Most importantly, it proves exactly how much revenue was actually recovered."*
