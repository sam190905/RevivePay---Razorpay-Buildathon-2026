# RevivePay — Antigravity Project Plan

## Purpose

RevivePay is a hackathon MVP for Razorpay's **AI Revenue Recovery** track.

Product promise:

> Detect failed/at-risk payments → understand why → estimate whether recovery is worthwhile → recommend a bounded recovery action → enforce deterministic guardrails → execute the allowed action through Razorpay Test Mode where supported → verify the outcome → measure recovered revenue → maintain a clear audit trail.

This is a **hackathon project, not a production fintech platform**.

Priority order:

**Working end-to-end flow > reliability > clear AI value > polished demo > optional features**

Do not overengineer.

---

# 1. MVP SCOPE

Focus primarily on **failed payments**.

Do not try to fully implement all of the following in the MVP:

- checkout abandonment
- subscriptions
- overdue invoices
- complex CRM
- multiple notification providers
- complex authentication
- microservices
- Kafka/Kubernetes
- RAG/vector database

The core demo is:

```text
Payment fails
      ↓
Razorpay webhook
      ↓
Recovery case created
      ↓
AI diagnoses failure
      ↓
Recovery probability / eligibility
      ↓
AI recommends an allowed action
      ↓
Deterministic policy check
      ↓
Allowed?
   /        \
 NO          YES
 ↓             ↓
Manual       Execute
Review       Recovery
               ↓
            Verify
               ↓
        Revenue recovered
               ↓
          Audit timeline
```

The product must clearly answer:

> **How much revenue did the AI actually recover?**

---

# 2. RECOMMENDED TECH STACK

## Backend

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- httpx

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Recharts or another lightweight chart library

## Database

- PostgreSQL

## AI

- OpenAI-compatible LLM API

## Payments

- Razorpay Test Mode APIs
- Razorpay Webhooks

Use **official Razorpay documentation as the source of truth**. Never invent API endpoints or request/response formats.

## Optional later

- scikit-learn / XGBoost for recovery probability
- Redis for background jobs
- LangGraph if it genuinely improves orchestration

Do not introduce optional infrastructure until the core flow is working.

---

# 3. ARCHITECTURE

Use a **single backend application**.

```text
                 ┌─────────────────────┐
                 │   Next.js Frontend  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    FastAPI Backend  │
                 └──────────┬──────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
     PostgreSQL         AI Service       Razorpay API
          │                 │                 │
          │                 │                 ▼
          │                 │             Webhooks
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    Recovery Engine
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          Policy / Guards         Action Executor
                                       │
                                       ▼
                                  Razorpay/Test
                                       │
                                       ▼
                                    Verify
                                       │
                                       ▼
                                 Audit + Metrics
```

Keep modules cleanly separated, but do not turn every module into a service.

---

# 4. AGENT DESIGN

Build one controlled **Recovery Agent**, not a free-form autonomous agent.

Workflow:

```text
1. Build payment/customer context
2. Diagnose failure
3. Estimate recovery likelihood
4. Recommend one allowed action
5. Pass recommendation to policy engine
6. Execute only if policy approves
7. Verify result
8. Record outcome
```

Allowed actions should be a fixed allowlist, for example:

```text
retry_payment
create_payment_link
send_recovery_reminder
manual_review
```

Only implement actions that are officially supported and appropriate for the selected Razorpay workflow.

The LLM must never directly execute arbitrary HTTP requests or arbitrary financial operations.

---

# 5. POLICY / GUARDRAIL ENGINE

This is mandatory and deterministic.

Example:

```text
LLM recommendation
       ↓
Schema validation
       ↓
Policy engine
       ↓
Eligible payment?
Retry limit OK?
Risk acceptable?
Amount within threshold?
Cooldown satisfied?
       ↓
APPROVE / BLOCK
```

Example policy result:

```json
{
  "allowed": true,
  "action": "retry_payment",
  "risk_level": "low",
  "reason": "Payment is eligible and retry limit has not been exceeded",
  "violated_rule": null
}
```

If blocked, route to `manual_review`; do not treat a policy block as an application failure.

The LLM cannot override policy.

---

# 6. AI OUTPUT CONTRACT

The AI should return structured data.

Example:

```json
{
  "classification": "temporary_failure",
  "confidence": 0.91,
  "recommended_action": "retry_payment",
  "reason": "The available payment context is more consistent with a temporary failure",
  "recommended_delay_minutes": 30
}
```

Requirements:

- Validate with Pydantic.
- Reject unknown actions.
- Reject malformed or incomplete output.
- Reject impossible values.
- On model failure, fall back safely to deterministic logic or `manual_review`.
- Do not store chain-of-thought.
- Store structured decisions and concise explanations only.

---

# 7. DATABASE — MVP

Start with these models:

## Customer

```text
id
external_customer_id
name
email
phone
created_at
updated_at
```

## Payment

```text
id
razorpay_payment_id
customer_id
order_id
amount
currency
status
method
failure_reason
failure_code
created_at
updated_at
```

## RecoveryCase

```text
id
payment_id
customer_id
amount_at_risk
reason
recovery_probability
status
recommended_action
actual_action
recovered_amount
opened_at
closed_at
```

## RecoveryAction

```text
id
recovery_case_id
action_type
status
amount
result
error
requested_at
executed_at
```

## AuditLog

```text
id
recovery_case_id
event_type
actor
action
status
metadata
timestamp
```

Add webhook/idempotency storage only as needed.

Do not build event sourcing.

---

# 8. RAZORPAY WEBHOOK FLOW

Implement an endpoint similar to:

```text
POST /webhooks/razorpay
```

Flow:

```text
Webhook received
      ↓
Verify signature
      ↓
Check event idempotency
      ↓
Persist event/update payment
      ↓
Create/update recovery case
      ↓
Trigger recovery workflow
      ↓
Return quickly
```

Requirements:

- verify webhook signatures
- prevent duplicate processing
- do not block the webhook request with long AI work
- handle malformed events safely
- never log secrets

Use official Razorpay documentation for exact webhook fields and signature behavior.

---

# 9. RECOVERY ACTIONS

Implement only one or two useful actions for the MVP.

Recommended:

### Action A — Smart Retry

Use only if the exact payment state and Razorpay API support the workflow.

### Action B — Recovery Payment Link

Use where officially supported and appropriate.

### Action C — Manual Review / Reminder

This can be an internal or simulated workflow.

Do not build several notification channels.

---

# 10. RECOVERY PROBABILITY

ML is optional for the MVP.

First implement a simple deterministic score using:

- payment history
- previous failure count
- transaction amount
- failure category
- customer history
- previous recovery result

Represent it as:

```text
recovery_probability = 0.84
```

Only after the complete product flow works should you consider Logistic Regression or XGBoost.

If ML is added:

- use synthetic data
- document that it is synthetic
- report metrics honestly
- do not claim synthetic performance equals production performance

---

# 11. REVENUE METRICS

These are core product metrics, not optional analytics.

Calculate from application state:

```text
Revenue at Risk
Recoverable Revenue
Recovery Attempted
Revenue Recovered
Recovery Rate
```

Example values are only illustrative:

```text
Revenue at Risk        ₹4,80,000
Eligible for Recovery  ₹3,10,000
Recovery Attempted     ₹2,40,000
Revenue Recovered      ₹1,92,000
Recovery Rate                80%
```

Never hardcode business metrics into the dashboard.

Clearly label simulated outcomes.

---

# 12. DEMO MODE

A deterministic demo mode is required so judging does not depend entirely on external behavior.

Implement these scenarios:

## Scenario 1 — Successful Recovery

```text
Failed payment
→ temporary failure
→ high recovery probability
→ policy approves recovery
→ success
→ money recovered
```

## Scenario 2 — Payment Link Recovery

```text
Failed payment
→ payment link recommended
→ link generated
→ simulated/customer completion
→ money recovered
```

## Scenario 3 — Guardrail Block

```text
High-value / low-confidence case
→ AI recommends recovery
→ policy blocks automation
→ manual review
→ ₹0 auto-recovered
```

## Scenario 4 — Duplicate Webhook

```text
First event  → processed
Second event → ignored
```

## Scenario 5 — Execution Failure

```text
Execution failed
→ audit event created
→ status = failed
→ recovered amount = 0
→ no false success
```

The demo must be repeatable.

---

# 13. FRONTEND — ONLY FOUR CORE SCREENS

## 1. Overview Dashboard

Show:

- Revenue at Risk
- Recoverable Revenue
- Revenue Recovered
- Recovery Rate
- Cases Processed
- recovery funnel
- recovery by action
- recent cases

## 2. Recovery Cases

Show:

- customer
- amount
- failure reason
- recovery probability
- recommended action
- policy result
- status

## 3. Recovery Case Detail

Show:

- amount
- failure reason
- recovery probability
- AI diagnosis
- recommended action
- policy decision
- execution result
- recovered amount

Also show a timeline:

```text
Payment failed
↓
Webhook received
↓
Case created
↓
AI diagnosis
↓
Recovery score
↓
Action selected
↓
Policy approved/blocked
↓
Execution
↓
Verification
↓
Revenue recovered
```

## 4. Demo Control

Allow the presenter to trigger the deterministic scenarios.

Do not build a giant admin portal.

---

# 14. UI / UX

Target style:

- premium fintech
- clean
- minimal
- high contrast
- clear typography
- compact but readable
- subtle transitions
- strong data hierarchy

Avoid:

- generic AI gradients
- excessive glassmorphism
- huge illustrations
- excessive animations
- chatbot-first UI
- decorative features with no product value

A judge should understand the product within 30 seconds.

---

# 15. MINIMUM API SURFACE

Create only what the MVP requires:

```text
GET  /health
GET  /api/dashboard/summary
GET  /api/recovery-cases
GET  /api/recovery-cases/{id}
POST /api/recovery-cases/{id}/process
POST /api/recovery-cases/{id}/approve
POST /api/demo/scenarios
POST /webhooks/razorpay
```

Add endpoints only when the product actually needs them.

Use FastAPI-generated OpenAPI docs.

---

# 16. TESTING

Keep testing focused but meaningful.

## Unit tests

At minimum:

- policy engine
- revenue calculation
- AI response validation
- duplicate event detection

## Integration tests

At minimum:

- webhook → payment update
- webhook → recovery case
- recovery case → agent decision
- policy → action

## End-to-end

Test:

```text
payment failure
→ webhook
→ recovery case
→ AI decision
→ policy approval
→ recovery action
→ verification
→ recovered revenue
```

Also test:

- blocked case
- failed action

Do not spend days building a huge test suite.

---

# 17. SECURITY

Implement:

- environment variables for secrets
- `.env.example`
- webhook signature verification
- idempotency
- input validation
- strict action allowlist
- no arbitrary LLM tool execution
- no secrets in logs

Do not build complex authentication unless required.

---

# 18. PROJECT STRUCTURE

Prefer:

```text
revivepay/
├── frontend/
├── backend/
├── scripts/
├── docs/
├── .env.example
├── docker-compose.yml
└── README.md
```

Backend:

```text
backend/app/
├── api/
├── models/
├── schemas/
├── services/
├── agents/
├── policies/
├── actions/
├── integrations/
├── db/
└── utils/
```

Keep it modular, but simple.

---

# 19. PHASE-BY-PHASE EXECUTION

**Never implement the entire project at once.**

At the end of each phase:

1. Implement only that phase.
2. Run relevant tests/checks.
3. Fix errors.
4. Provide the phase report.
5. Stop and wait for the next instruction.

Do not silently move to future phases.

---

## PHASE 0 — Inspect + Bootstrap

Tasks:

- inspect repository before changing anything
- preserve useful existing work
- establish frontend/backend structure
- configure environment variables
- create `.env.example`
- configure database connection
- create `/health`
- create basic frontend shell
- create README setup instructions
- verify Docker/PostgreSQL if the repository uses Docker

Acceptance criteria:

```text
Frontend runs
Backend runs
Database connection works
/health works
Environment config is documented
```

Stop after Phase 0.

---

## PHASE 1 — Database + Seed Data

Implement:

- SQLAlchemy models
- Alembic migrations
- Pydantic schemas
- seed script
- sample customers
- sample failed payments
- sample recovery cases

Acceptance criteria:

```text
Database can be initialized from scratch
Seed script works
Models can be queried
Basic tests pass
```

Stop after Phase 1.

---

## PHASE 2 — Razorpay Test Mode + Webhooks

Tasks:

- configure Razorpay credentials
- implement the official API client methods actually needed
- implement webhook endpoint
- verify signature
- implement event idempotency
- handle API errors/timeouts

Acceptance criteria:

```text
Webhook can be received locally
Signature verification works
Duplicate events are ignored
Razorpay integration is isolated in a service
```

If live credentials are unavailable, implement and test the interfaces/mock adapter without claiming live API validation.

Stop after Phase 2.

---

## PHASE 3 — Recovery Case Pipeline

Implement:

```text
payment failure
→ payment update
→ recovery case
→ audit event
```

Acceptance criteria:

- failed payment creates a recovery case
- database state is correct
- audit event exists
- duplicate webhook does not create duplicate cases

Stop after Phase 3.

---

## PHASE 4 — Deterministic Recovery Engine

Before the LLM, make the workflow function deterministically.

Implement:

- failure classification baseline
- recovery score baseline
- eligibility rules
- policy engine
- allowed action list
- action execution abstraction
- verification
- revenue calculation

Acceptance criteria:

```text
Payment
→ diagnosis
→ recovery score
→ policy
→ action
→ verification
→ revenue result
```

works reliably.

Stop after Phase 4.

---

## PHASE 5 — AI Recovery Agent

Add the LLM.

Implement:

- structured prompt
- structured output schema
- diagnosis
- action recommendation
- concise explanation
- confidence
- fallback behavior

The LLM only chooses from allowed actions.

Acceptance criteria:

```text
Case context
→ LLM
→ structured decision
→ validation
→ policy
```

works reliably.

Stop after Phase 5.

---

## PHASE 6 — Recovery Execution

Implement the selected Razorpay/Test Mode recovery action(s) that are valid for the workflow.

Also implement deterministic simulation adapters for the demo.

Acceptance criteria:

- success recorded correctly
- failure recorded correctly
- blocked actions never execute
- recovered amount is outcome-based

Stop after Phase 6.

---

## PHASE 7 — Dashboard + Case Detail

Implement:

- Overview
- Recovery Cases
- Case Detail
- Demo Control

All metrics must come from backend data.

Acceptance criteria:

A judge can understand the product without reading source code.

Stop after Phase 7.

---

## PHASE 8 — Demo Scenarios + Polish

Implement the five scenarios:

- successful recovery
- payment link recovery
- blocked recovery
- duplicate webhook
- failed execution

Then polish:

- loading states
- errors
- empty states
- charts
- status badges
- audit timeline
- responsive layout

Acceptance criteria:

The demo can be repeated reliably.

Stop after Phase 8.

---

## PHASE 9 — Final Testing + Documentation

Run:

- unit tests
- integration tests
- end-to-end happy path
- blocked path
- failed action path
- frontend production build
- backend startup
- clean database migration

Create/update:

```text
README.md
ARCHITECTURE.md
API.md
DEMO_SCRIPT.md
```

Stop after Phase 9.

---

# 20. OPTIONAL FEATURES — ONLY AFTER MVP

Only if the MVP is stable and there is enough time:

1. ML recovery probability model
2. Redis background jobs
3. LangGraph orchestration
4. subscription recovery
5. checkout abandonment recovery
6. notification integrations
7. richer analytics

Never compromise the core demo to build optional features.

---

# 21. FINAL 3-MINUTE DEMO

## 0:00–0:20 — Problem

Show revenue at risk.

Explain:

> Payment failure does not always mean permanent revenue loss.

## 0:20–0:50 — Trigger

Trigger a failed-payment scenario.

## 0:50–1:20 — AI Diagnosis

Show:

- failure classification
- recovery probability
- recommended action

## 1:20–1:50 — Guardrail

Show:

```text
Policy check → APPROVED
```

or demonstrate:

```text
Policy check → BLOCKED → Manual Review
```

## 1:50–2:20 — Execute + Verify

Run the Razorpay/Test Mode or deterministic simulated recovery.

## 2:20–2:40 — Business Impact

Show:

```text
Revenue at Risk
↓
Recovery Attempted
↓
Revenue Recovered
```

## 2:40–3:00 — Audit Trail

Show:

```text
Webhook
→ Diagnosis
→ Score
→ Decision
→ Policy
→ Execution
→ Verification
→ Recovery
```

Suggested closing statement:

> **“RevivePay does not just detect failed payments. It decides which revenue is worth recovering, acts within deterministic guardrails, and proves how much revenue it recovered.”**

---

# 22. NON-NEGOTIABLE RULES

1. Inspect before changing anything.
2. Do not delete useful existing work.
3. Do not implement future phases early.
4. Never fabricate Razorpay APIs.
5. Use official Razorpay docs for API behavior.
6. Never let the LLM directly control arbitrary financial operations.
7. Validate every AI response.
8. Keep policy enforcement deterministic.
9. Never hardcode business metrics.
10. Clearly label synthetic/simulated data.
11. Never claim an external integration was tested when it was not.
12. Prefer a working simple solution over a sophisticated incomplete one.
13. Do not introduce Redis/ML/LangGraph unless earlier phases are stable.
14. Do not create unnecessary microservices.
15. Do not store chain-of-thought.
16. Test each phase before proceeding.
17. Debug failures before adding more features.
18. Keep the application runnable locally.
19. Do not substitute fake success for a real or clearly labeled simulation.
20. If a requirement is ambiguous, choose the simplest approach consistent with the hackathon scope and document the decision.

---

# 23. PHASE REPORT FORMAT

At the end of every phase, use exactly this structure:

```text
PHASE: <number + name>

STATUS:
Completed / Blocked

WHAT WAS IMPLEMENTED:
- ...

FILES CREATED:
- ...

FILES MODIFIED:
- ...

TESTS RUN:
- ...

MANUAL TEST:
1. ...
2. ...
3. ...

KNOWN ISSUES:
- ...

CURRENT PROJECT STATE:
...

NEXT PHASE:
...
```

Do not claim something works unless you actually tested it.

Clearly distinguish:

```text
Implemented and locally tested
```

from:

```text
Requires Razorpay credentials / external service
```

---

# 24. HOW ANTIGRAVITY SHOULD USE THIS FILE

This file is the persistent source of truth for the RevivePay hackathon project.

At the beginning of every new work session:

1. Read this file before making changes.
2. Inspect the current repository state.
3. Determine the last completed phase from the repository and previous reports.
4. Do not assume that a phase is complete without checking its acceptance criteria.
5. Resume from the first incomplete phase.
6. Do not restart completed work unless verification shows it is broken.
7. Do not skip phases.

If the user explicitly tells you to redo or change the plan, follow the user's newer instruction and update this file when appropriate.

---

# CURRENT PROJECT STATE

Update this section after every completed phase.

```text
Current phase: Phase 7
Last completed phase: Phase 7
Next phase: Phase 8 — Demo Scenarios + Polish
Status: Phase 7 verified complete
```

Keep this section current so a new Antigravity session can resume without needing the full history of the chat.
