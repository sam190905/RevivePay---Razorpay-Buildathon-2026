# REVIVEPAY — PROJECT SUMMARY

This document describes the **ACTUAL CURRENT IMPLEMENTATION** of the RevivePay project. It is intended to serve as the factual source of truth for generating hackathon pitch materials and demo scripts.

---

## 1. PROJECT OVERVIEW

**What it is:** RevivePay is an AI-powered automated revenue recovery system built on top of Razorpay. 
**The problem it solves:** E-commerce and SaaS merchants lose massive amounts of revenue to "silent leaks"—payments that fail at checkout and are never recovered. 
**Target users:** Any merchant using Razorpay who wants to maximize conversion and stop losing revenue to temporary failures, insufficient funds, or customer errors.
**Core value proposition:** It detects failures instantly via webhooks, uses AI (Google Gemini) to diagnose the failure reason, applies deterministic business guardrails to prevent risky actions, and automatically executes a recovery action (like sending a new payment link) to save the sale.

## 2. PROBLEM STATEMENT

When a payment fails on a standard checkout, the merchant's dashboard simply logs "Payment Failed." Because the merchant lacks the context to act, the customer usually abandons the cart, leading to permanent revenue loss. Manual recovery (calling or emailing the customer) is unscalable, slow, and inefficient. Furthermore, different failures require different handling: a "Gateway Timeout" should trigger an immediate automated retry link, whereas a "Suspected Fraud" failure should be blocked and manually reviewed. Without intelligent automation, merchants leave money on the table.

## 3. SOLUTION

RevivePay provides an end-to-end, fully automated recovery pipeline:
1. **Payment Failure:** Razorpay sends a `payment.failed` webhook.
2. **Case Creation:** The system creates a tracking case for the failed transaction.
3. **AI Diagnosis:** The AI Agent analyzes the failure code, reason, and context to classify the error and recommend a recovery action.
4. **Recovery Policy:** A deterministic Policy Engine evaluates the AI's recommendation against business rules (e.g., amount ceilings, fraud blocks).
5. **Recovery Action:** The Action Executor triggers the approved action (e.g., generating a Razorpay Payment Link).
6. **Recovery Outcome:** When the customer pays the link, a `payment_link.paid` webhook closes the case as recovered.
7. **Audit:** Every step is logged immutably in a granular audit timeline.

## 4. END-TO-END USER FLOW

**Actual Implemented Flow:**
1. A `payment.failed` webhook is received by the FastAPI backend (verified via HMAC).
2. The payload is parsed; a `Customer`, `Payment`, and `RecoveryCase` are created in Postgres.
3. The AI Agent is invoked with the failure details and customer email.
4. The AI returns a structured JSON response containing: classification (e.g., `fraud`, `insufficient_funds`), confidence score, and a recommended action (`create_payment_link` or `manual_review`).
5. The Policy Engine runs. If the amount is > ₹5,000 or the classification is `fraud`, it overrides the AI and forces `manual_review`.
6. If approved, the Action Executor generates an actual Razorpay Payment Link via the Razorpay API (if keys are provided) or a simulated link (in Developer Mode).
7. The Dashboard metrics update live.
8. If the customer pays (simulated via Demo Control or real via Razorpay webhook), the system verifies the amount and updates the case to `recovered`.

## 5. AI / INTELLIGENCE LAYER

**Where AI is used:** In the `AIRecoveryAgent` to diagnose the root cause of the failure and recommend an action.
**Provider & Model:** Google Gemini (`gemini-1.5-flash`) via the `google-genai` SDK, with support for OpenAI via Structured Outputs. 
**Inputs:** Payment amount, currency, error code, error description, and customer email.
**Outputs:** Strict JSON matching the `AIDiagnosisResult` schema (classification, confidence, recommended action from an allowlist, concise reason).
**Fallback / Deterministic Mode:** If the `GEMINI_API_KEY` is missing, invalid, or the API is unreachable, the system gracefully degrades to a **Deterministic Fallback**. It maps error codes (e.g., `FRAUD` → `manual_review`, `GATEWAY_ERROR` → `create_payment_link`) to ensure the recovery pipeline never stalls. 
**Transparency:** The UI explicitly tags every diagnosis as either `AI_AGENT` or `SYSTEM_FALLBACK` so the merchant knows exactly who made the decision.

## 6. RECOVERY ACTIONS

Currently, two actions are fully implemented in the `RecoveryActionType` enum:
- **`create_payment_link`**: Automatically generates a new payment link to capture the funds. If real Razorpay keys are configured, it hits the Razorpay REST API. If not, it simulates the link creation for demo purposes.
- **`manual_review`**: Halts the automated pipeline. The case remains open and is flagged for human intervention in the dashboard.

## 7. RAZORPAY INTEGRATION

- **Webhooks:** The `/webhooks/razorpay` endpoint actively listens for `payment.failed` and `payment_link.paid`. It implements strict HMAC-SHA256 signature verification and idempotency (tracking `X-Razorpay-Event-Id`) to safely ignore duplicate webhooks.
- **REST API:** The Action Executor uses `httpx` to call `https://api.razorpay.com/v1/payment_links` using Basic Auth with the `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` to generate live Test Mode links.
- **Graceful Degradation:** If keys are missing, the system seamlessly mocks the API response, allowing the entire application to be run and demonstrated locally without a real Razorpay account.

## 8. DEMO MODE

A comprehensive Demo Mode is implemented to reliably present the project without needing live transactions or Ngrok webhook tunnels.
- **How it works:** The `/demo/scenarios` API constructs synthetic Razorpay webhook payloads and signs them with the local HMAC secret. It posts these payloads to its own webhook endpoint, perfectly simulating a live Razorpay event.
- **Scenarios:** 
  1. *Successful Recovery*: Standard failure → Link creation.
  2. *Payment Link Recovery*: Customer-action failure (insufficient funds).
  3. *Guardrail Block*: Forces a `FRAUD` error code to demonstrate the Policy Engine blocking the AI.
  4. *Execution Failure*: Simulates a Razorpay downtime error.
  5. *Duplicate Webhook*: Fires the same webhook twice to demonstrate idempotency.

## 9. FRONTEND

- **Framework:** Next.js 14 (App Router), React, TypeScript.
- **Styling:** Tailwind CSS with a premium glassmorphism aesthetic.
- **Theme:** Dynamic Light (Cloud/Sky background) and Dark (Starry background) themes that switch instantly without reloads.
- **Components:** Uses Lucide React for iconography. Clean, component-based architecture (e.g., `<SearchCommand />`, `<TopNav />`).
- **State:** React hooks + Axios for API communication. Live polling for real-time dashboard updates.

## 10. DASHBOARD

The Overview dashboard (`/`) pulls live, aggregated data from the Postgres database via `GET /dashboard/summary`:
- **Revenue at Risk:** Total amount of failed payments.
- **Recoverable:** Amount that passed policy guardrails.
- **Recovery Attempted:** Amount where actions were executed.
- **Recovered:** Amount successfully paid by customers.
- **Recovery Rate:** Percentage metric of recovered vs at-risk.
- **Recovery Funnel:** Horizontal bar charts showing the drop-off from Failed → Diagnosed → Approved → Executed.
- **Recovery Actions:** Donut chart of actions taken.
- **Recent Cases:** Top 5 recent cases with status badges.
*(Note: Numbers are calculated from real DB data, but during a demo, this data is generated by the Demo Control scenarios).*

## 11. RECOVERY CASES

The `/cases` page shows a tabular list of all recovery cases. It polls the backend every 5 seconds. It displays customer details, amounts, failure reasons, AI recommendations, actual actions executed, and current status (e.g., `open`, `processing`, `recovered`, `manual_review`). 

## 12. CASE DETAILS

The `/cases/[id]` page provides a deep dive into a specific case:
- **Progress Tracker:** Visual stepper (Failed → Created → Diagnosis → Policy → Action → Verification).
- **AI Diagnosis Card:** Shows the AI's classification, confidence score, recommendation, and the Policy Engine's final verdict (Outcome, Risk Level, Violated Rule).
- **Action Card:** Shows the generated payment link URL.
- **Audit Timeline:** A chronological list of every micro-event in the case's lifecycle, complete with raw expandable JSON payloads for debugging.

## 13. SEARCH / COMMAND PALETTE

- **Trigger:** Clicking the search bar or pressing `⌘K` / `Ctrl+K`.
- **UI:** A full-screen backdrop-blurred overlay with a glassmorphism modal.
- **Scope:** Real-time debounced queries hitting the backend `ILIKE` search. It searches customer names, emails, payment IDs, failure reasons, case statuses, UUIDs, and exact amounts.
- **UX:** Full keyboard navigation (`↑` `↓` `Enter` `Esc`) to jump directly to a case detail page.

## 14. DEMO CONTROL

The `/demo` page provides a control panel for presentations:
- **Trigger Scenarios:** Buttons to instantly fire any of the 5 synthetic webhook scenarios.
- **Simulate Payment:** A button available on Case Detail pages (in simulated mode) that fires a synthetic `payment_link.paid` webhook, completing the recovery loop so presenters can demonstrate a successful recovery in 10 seconds.

## 15. BACKEND / ARCHITECTURE

```text
Next.js Frontend (React/Tailwind)
       ↓ (REST APIs)
FastAPI Backend (Python 3.12)
       ├── Webhook Handler (HMAC Verification, Idempotency)
       ├── AI Agent (Gemini API / Fallback)
       ├── Policy Engine (Deterministic Guardrails)
       └── Action Executor (Razorpay API / Simulator)
       ↓
PostgreSQL DB (Async SQLAlchemy)
```

## 16. DATABASE / DATA MODEL

- `Customer`: Contact info.
- `Payment`: Raw Razorpay failure data (amount, error codes).
- `RecoveryCase`: The core workflow entity linking a payment to its recovery status.
- `RecoveryAction`: Records of executed actions (e.g., the generated payment link ID).
- `AuditLog`: Immutable ledger of events (`case_created`, `ai_diagnosed`, `policy_evaluated`).
- `WebhookEvent`: Stores payload hashes and Razorpay Event IDs for idempotency.

## 17. API ENDPOINTS

- `GET /recovery-cases`: List all cases.
- `GET /recovery-cases/search?q=...`: Global search.
- `GET /recovery-cases/{id}`: Full case details + audit logs.
- `GET /dashboard/summary`: Aggregated metrics and funnel data.
- `POST /webhooks/razorpay`: Live webhook receiver.
- `POST /demo/scenarios`: Triggers synthetic webhooks.
- `POST /demo/scenarios/simulate-payment`: Triggers synthetic paid webhooks.

## 18. TECH STACK

| Technology | Purpose | Where Used |
|---|---|---|
| **Next.js 14** | Frontend framework | Web UI |
| **Tailwind CSS** | Styling & Glassmorphism | Web UI |
| **FastAPI** | Backend framework | API & Webhook processing |
| **PostgreSQL** | Database | Data persistence |
| **SQLAlchemy** | ORM (Async) | Database interaction |
| **Google Gemini** | AI LLM | Failure diagnosis & recommendations |
| **Razorpay API** | Payments | Webhooks & Payment Link generation |

## 19. WHAT IS ACTUALLY WORKING

✅ Razorpay Webhook Verification & Idempotency
✅ AI Diagnosis via Google Gemini (Strict JSON)
✅ Deterministic AI Fallback & Policy Guardrails
✅ Razorpay Payment Link Creation (Real Test Mode API)
✅ Live Dashboard Metrics & Aggregation
✅ ⌘K Global Search
✅ Dark/Light Theme Switching with Glassmorphism
✅ End-to-End Demo Simulation

## 20. KNOWN LIMITATIONS / WHAT BROKE

**Challenge:** LLMs are prone to hallucinating actions or returning invalid JSON, which is dangerous in a financial pipeline.
**Solution:** We forced the LLM to use structured JSON outputs strictly mapped to Pydantic schemas. Furthermore, we decoupled intelligence from execution by building a deterministic **Policy Engine** that evaluates the AI's output. If the AI suggests recovering a fraudulent transaction, the Policy Engine overrides it and forces a manual review.

**Challenge:** Demonstrating webhook-based products at hackathons is notoriously difficult because it requires live transactions, Ngrok tunnels, and dealing with third-party API latency.
**Solution:** We built a dedicated Demo Simulator that injects synthetic webhooks locally using our own HMAC secret. It perfectly mimics Razorpay's behavior, allowing for flawless, instantly repeatable live demos without external dependencies.

## 21. DEMO PREPARATION

**Ideal Sequence:**
1. Start the app. Open the Dashboard (Metrics will be ₹0).
2. Open the **Demo Control** page. Click **"Successful Recovery"**.
3. Quickly navigate back to the Dashboard. Watch the metrics instantly jump as the webhook is processed.
4. Go to **Recovery Cases**, click the new case.
5. Show the **Progress Tracker**, the **AI Diagnosis** (pointing out the AI vs Policy decision), and the generated **Payment Link**.
6. Click **Simulate Customer Payment** in the action card.
7. Go back to the Dashboard and show that "Revenue Recovered" has increased and the Recovery Rate chart has updated.

## 22. HACKATHON PITCH MATERIAL

**A. One-line description:** An AI-powered revenue recovery engine that automatically rescues failed Razorpay transactions before you even know they failed.
**B. 30-second elevator pitch:** Every day, merchants lose thousands to failed payments due to insufficient funds or gateway timeouts. RevivePay acts as an automated financial paramedic. It catches failed payments in milliseconds, uses Gemini AI to diagnose the root cause, checks business guardrails, and instantly sends the customer a new payment link—turning lost sales into recovered revenue automatically.
**C. Key differentiators:** We don't just use AI; we use AI safely. Our architecture pairs a generative AI diagnostician with a deterministic policy engine, ensuring automated recovery never executes risky or fraudulent actions.
**D. Strongest technical points:** Real-time async webhook processing, robust idempotency, seamless failover from LLM to deterministic rules, and a fully functional live Razorpay API integration.

## 23. FILE / CODE REFERENCES

- **Backend AI Agent:** `backend/app/services/ai_agent.py` (Gemini API integration & mock fallback).
- **Policy Engine:** `backend/app/services/policy_engine.py` (Deterministic guardrails overriding AI).
- **Webhook Handler:** `backend/app/api/webhooks.py` (HMAC validation & Idempotency).
- **Demo API:** `backend/app/api/demo.py` (Synthetic webhook injection).
- **Frontend Search:** `frontend/app/components/search-command.tsx` (⌘K modal).
- **Frontend Dashboard:** `frontend/app/page.tsx` (Live metric rendering).
