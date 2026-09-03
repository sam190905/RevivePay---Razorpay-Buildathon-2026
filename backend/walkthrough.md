# Phase 8 Fixes: UI Synchronization and Developer Mode

## What changed

1. **Recovery Lifecycle and the `PROCESSING` State**
   - Updated `recovery_engine.py` to synchronously set `case.status = "processing"` before triggering the Gemini API call. This prevents cases from lingering in an inaccurate `OPEN` state.
   - Stopped `process_recovery_case` from prematurely setting `case.status = "recovered"` upon Payment Link creation. The case correctly remains in `PROCESSING` while waiting for the customer to pay, moving to `RECOVERED` only when the `payment_link.paid` webhook arrives.

2. **Asynchronous Polling UX**
   - Added `setInterval` polling to both `frontend/app/cases/page.tsx` and `frontend/app/cases/[id]/page.tsx`.
   - The polling fires every 2 seconds but *only* if the case (or at least one case in the list) is in the `OPEN` or `PROCESSING` state. Polling stops automatically once a terminal state is reached.

3. **Progress Tracker UI**
   - Added a dynamic visual step indicator on the Case Details page to map out the real state of the case based on Audit Logs, instead of arbitrary timers.
   - Shows **"AI Recovery in Progress"** with a spinner while processing, and **"Waiting for customer payment"** after the payment link is generated.

4. **App Mode Architecture (`developer` vs `test`)**
   - Transitioned from `demo_mode` boolean to an explicit `APP_MODE` environment variable.
   - `APP_MODE=developer`: Bypasses all Gemini LLM usage and Razorpay API calls natively by instantiating mock providers in `ai_agent.py` and `action_executor.py`. All business logic, DB records, and webhooks function exactly identical to production.
   - `APP_MODE=test`: Allows live external testing of the Gemini integration and Razorpay test endpoints without affecting production analytics.

## What was verified

1. **Test Mode (Gemini)**: Executed `$env:APP_MODE="test"; python -m scripts.test_gemini`, validating that Gemini responds correctly with proper formatting and structure.
2. **Developer Mode**: Re-ran the existing unit test suite in developer mode (`test_phase6.py` and `test_phase3.py`) ensuring zero external calls while simulating the full deterministic fallback process.
3. **Guardrails**: Confirmed policy rules remain completely decoupled from the scenarios. Fraud blocks correctly generate `MANUAL_REVIEW`.
4. **Execution API failure behavior**: Ensured error propagation in mocked backend executions operates exactly identically as before.
