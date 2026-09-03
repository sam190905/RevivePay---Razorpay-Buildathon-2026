# Implementation Plan: Fix Premature Recovery & Add Developer Mode

## Goal Description
Resolve UI synchronization issues where cases appear as `RECOVERED` prematurely and lack a visible `PROCESSING` state. Add a deterministic `developer` mode that safely bypasses external API calls while preserving the complete business workflow.

## User Review Required
- **App Mode Configuration**: Introducing `APP_MODE` (developer/test) to override `demo_mode`. The `developer` mode will forcefully mock both the Gemini AI call and the Razorpay API call, while `test` mode will use the real keys if available.
- **Frontend Polling**: Implementing a 2-second polling interval on the `/cases` and `/cases/[id]` pages. It only polls if there are cases in the `open` or `processing` states, saving resources.

## Proposed Changes

---

### Backend Configuration & App Mode

#### [MODIFY] backend/app/config.py
- Add `app_mode: str = Field(default="developer", env="APP_MODE")`
- Maintain `demo_mode` temporarily if needed but transition logic to use `app_mode`.

#### [MODIFY] backend/app/services/ai_agent.py
- Update `self.is_mock = ... or settings.app_mode == "developer"`. This ensures zero external Gemini API calls in developer mode.

#### [MODIFY] backend/app/services/action_executor.py
- Change `if settings.demo_mode:` to `if settings.app_mode == "developer":` to mock Razorpay links in developer mode. Ensure zero external Razorpay API calls.

---

### Backend Engine Lifecycle

#### [MODIFY] backend/app/services/recovery_engine.py
- Inside `process_recovery_case`, instantly set `case.status = "processing"` and `await db.commit()` at the very beginning of the function. This ensures the database accurately reflects the processing state before the synchronous LLM/Policy engine blocks.
- Ensure that upon successful `action_executor.execute`, the case status remains `processing` (it's waiting for the payment verification). It should NOT jump to `recovered`.

---

### Frontend State-Aware UX

#### [MODIFY] frontend/app/cases/page.tsx
- Add a React `useEffect` with `setInterval` to poll `fetchRecoveryCases` every 2 seconds.
- Only poll if `cases.some(c => c.status === "open" || c.status === "processing")`.

#### [MODIFY] frontend/app/cases/[id]/page.tsx
- Add a 2-second polling interval for `fetchCaseDetail` if `data.case.status === "open" || data.case.status === "processing"`.
- Implement the "AI Recovery in Progress" animated UI.
- Add a visual step indicator based on audit logs (`case_created`, `ai_diagnosis`, `policy_check`, `action_executed`, `verification`).

## Verification Plan
1. **Developer Mode**: Run `APP_MODE=developer`, trigger a successful recovery, and verify no external calls are made and the UI correctly polls through the processing states.
2. **Real/Test Mode**: Run `APP_MODE=test` with Gemini, ensure external calls are made, and verify the UI shows real-time updates as the Gemini diagnosis completes.
3. **Guardrail Check**: Verify the policy block scenario correctly halts execution and displays `MANUAL_REVIEW`.
