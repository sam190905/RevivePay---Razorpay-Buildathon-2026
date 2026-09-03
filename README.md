# RevivePay

**AI-powered revenue recovery system for Razorpay.** Detects failed payments in real time, diagnoses failure causes using AI (Gemini) or deterministic fallback, estimates recovery probability, enforces policy guardrails, executes recovery actions, and proves how much revenue was actually recovered — end to end.

---

## ✨ Feature Highlights

### 🤖 AI-Powered Diagnosis
- **Gemini LLM Integration** — When a `GEMINI_API_KEY` is configured, cases are diagnosed via Google Gemini. The AI classifies the failure (e.g. `temporary`, `customer_action`, `fraud`), estimates recovery probability, and recommends an action.
- **Deterministic Fallback** — When no AI key is available or the LLM call fails, a rule-based engine takes over. It maps error codes to classifications, assigns confidence scores, and recommends actions — guaranteeing the pipeline never stalls.
- **Decision Source Tagging** — Every diagnosis is tagged `ai_agent` or `system_fallback` so operators always know which engine made the call.

### 🛡️ Policy Engine with Guardrails
A deterministic policy engine evaluates every AI recommendation before execution:
- **Fraud Block** — Transactions flagged as `fraud` are always blocked and routed to manual review.
- **Recovery Score Threshold** — Cases with recovery probability below `0.2` are blocked.
- **Amount Ceiling** — Transactions above ₹5,000 (500,000 paise) require manual review.
- **Action Restrictions** — Only `create_payment_link` is permitted for automated execution; all other actions route to manual review.
- **Outcomes** — `APPROVE`, `BLOCK`, or `MANUAL_REVIEW`, each logged with risk level and violated rule.

### ⚡ Recovery Actions
- **Payment Link Creation** — Generates a Razorpay payment link (real or simulated) and sends it to the customer.
- **Real Razorpay Test Mode** — When `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` are set, the system creates actual Razorpay test-mode payment links via the Razorpay API.
- **Simulated Developer Mode** — When Razorpay keys are absent, a simulated link is generated so the full pipeline can be demoed without real API credentials.
- **Recovery Verification** — When a payment link is paid (via webhook or manual sync), the system verifies the amount and updates the case status to `recovered` or `partially_recovered`.

### 🔗 Webhook Handling
- **HMAC-SHA256 Verification** — Every incoming Razorpay webhook is signature-verified using the configured `RAZORPAY_WEBHOOK_SECRET`.
- **Idempotency** — Duplicate webhook events (same `X-Razorpay-Event-Id`) are detected and safely ignored.
- **Supported Events** — `payment.failed` (triggers recovery pipeline), `payment_link.paid` (triggers recovery verification), `payment.captured` (acknowledged but not processed).

### 📊 Dashboard (Overview Page)
- **Revenue Metrics** — Revenue at Risk, Recoverable Revenue, Recovery Attempted, Revenue Recovered.
- **Recovery Rate** — Percentage of at-risk revenue successfully recovered, with a visual progress bar.
- **Cases Processed** — Total recovery cases handled.
- **Recovery Funnel** — Horizontal bar chart showing conversion from failed payments → diagnosed → policy-approved → action taken → recovered.
- **Action Distribution** — Donut chart showing the breakdown of recovery actions (`create_payment_link`, `manual_review`, etc.).
- **Recent Cases** — Quick-glance list of the 5 most recent cases with status badges and amounts.
- **System Status Footer** — Live indicators for AI Agent, Razorpay API, and Webhook Tunnel.

### 🔍 Global Transaction Search
- **Command Palette** — A full search modal triggered by clicking the search bar or pressing `⌘K` / `Ctrl+K`.
- **Search Scope** — Searches across customer name, email, Razorpay payment ID, case status, failure reason, failure code, recommended/actual action, case ID (UUID), and amount (rupees → paise conversion).
- **Debounced API Calls** — 300ms debounce to avoid excessive requests.
- **Rich Results** — Each result shows customer name, email, status badge, amount, failure reason, and case ID.
- **Keyboard Navigation** — `↑↓` to navigate, `Enter` to open, `Escape` to close.
- **Click-to-Navigate** — Clicking a result navigates directly to `/cases/{id}`.

### 📋 Recovery Cases List
- **Live Polling** — Automatically refreshes every 5 seconds.
- **Status Badges** — Color-coded badges for `open`, `processing`, `recovered`, `partially_recovered`, `failed`, `manual_review`.
- **Tabular View** — Customer name, email, amount, currency, failure reason, recovery probability, recommended action, actual action, status, opened date, and recovered amount.

### 📄 Case Detail Page
- **Progress Tracker** — Visual step-by-step pipeline: Payment Failed → Case Created → AI Diagnosis → Policy Check → Recovery Action → Verification. Each step shows its current state (completed / processing / pending / failed).
- **Recovery Outcome Banner** — Context-aware banners for Recovered (green), Failed (red), and Manual Review (amber).
- **Overview Card** — Customer info, Razorpay Payment ID, failure reason/code, recovered amount, timestamps.
- **AI Diagnosis Card** — Classification, confidence bar, recommended action, decision source (Gemini vs Deterministic), and policy decision with outcome, risk level, reason, and violated rule.
- **Recovery Action Card** — Action type, execution status, mode (Real Test Mode vs Simulated Demo), provider ID, payment link URL, and recovered amount.
- **Simulate Payment Button** — In simulated mode, lets operators trigger a "customer payment" to verify the full recovery flow.
- **Sync Payment Status** — In real test mode, fetches the latest payment link status from Razorpay.
- **Audit Timeline** — Chronological log of every event with icons, timestamps, actors, descriptions, key-value details, and collapsible raw JSON.

### 🎮 Demo Control Panel
Five pre-built scenarios accessible from the Demo Control page:
1. **Successful Recovery** — Basic retry via payment link; payment fails, AI diagnoses, policy approves, link created, payment recovered.
2. **Payment Link Recovery** — Happy path through `INSUFFICIENT_FUNDS`; demonstrates customer-action-needed flow.
3. **Guardrail Block** — AI diagnosis returns fraud classification; policy engine blocks and routes to manual review.
4. **Execution Failure** — Simulated Razorpay downtime; demonstrates graceful failure handling.
5. **Duplicate Webhook** — Sends the same `payment.failed` webhook twice; validates idempotency.

### 🌗 Dark / Light Theme Toggle
- Persistent theme preference stored in `localStorage`.
- Light mode: Cloud/Sky gradient background with white glassmorphism cards.
- Dark mode: Deep night background with starfield particles and translucent cards.
- Smooth 500ms CSS transitions between modes.

---

## 🏗️ Architecture

```
Next.js Frontend (TypeScript + Tailwind)
    ↕ REST API (axios)
FastAPI Backend (Python 3.12+)
    ├── AI Agent Service → Gemini API / Deterministic Fallback
    ├── Policy Engine → Deterministic guardrails
    ├── Action Executor → Razorpay API / Simulated links
    ├── Recovery Engine → Orchestrates the full pipeline
    └── PostgreSQL (SQLAlchemy async)
```

### Database Models

| Model | Purpose |
|---|---|
| `Customer` | Stores customer info (name, email, phone) |
| `Payment` | Razorpay payment details (amount, currency, failure code/reason) |
| `RecoveryCase` | The core entity linking a failed payment to its recovery journey |
| `RecoveryAction` | Records executed actions (type, provider ID, result, status) |
| `AuditLog` | Immutable timeline events with structured metadata JSON |
| `WebhookEvent` | Stores raw webhook payloads for idempotency checks |

### Key Services

| Service | Description |
|---|---|
| `ai_agent.py` | Gemini LLM integration with deterministic fallback |
| `policy_engine.py` | Rule-based guardrails (fraud, risk, amount, action type) |
| `action_executor.py` | Executes recovery actions (real/simulated payment links) |
| `recovery_engine.py` | Orchestrates diagnosis → policy → execution → verification |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (for PostgreSQL)

### 1. Clone & Configure

```bash
cp .env.example .env
# Edit .env with your credentials (see Environment Variables below)
```

### 2. Start Database

```bash
docker-compose up -d
```

### 3. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Verify

| Endpoint | URL |
|---|---|
| Backend Health | http://localhost:8000/health |
| API Docs (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

---

## ⚙️ Environment Variables

See `.env.example` for all required configuration. Key variables:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `RAZORPAY_KEY_ID` | No | Enables real Razorpay Test Mode payment links |
| `RAZORPAY_KEY_SECRET` | No | Razorpay API secret |
| `RAZORPAY_WEBHOOK_SECRET` | Yes | HMAC secret for webhook signature verification |
| `GEMINI_API_KEY` | No | Enables AI-powered diagnosis via Google Gemini |
| `FRONTEND_URL` | No | CORS origin (defaults to `http://localhost:3000`) |

---

## 🧪 Testing

Backend test suite ensures stability and idempotency:

```bash
cd backend
python -m scripts.test_webhook
```

> **Note:** OpenAI/Gemini API keys are intentionally disabled during regression testing to ensure the deterministic fallback and core policies function correctly without external dependencies.

---

## 📁 Project Structure

```
├── frontend/                  # Next.js + TypeScript + Tailwind
│   ├── app/
│   │   ├── components/        # TopNav, Sidebar, SearchCommand, ThemeProvider
│   │   ├── cases/             # Recovery cases list + [id] detail page
│   │   ├── demo/              # Demo control panel
│   │   ├── globals.css        # Design tokens, theme vars, background effects
│   │   ├── layout.tsx         # Root layout with TopNav + ThemeProvider
│   │   └── page.tsx           # Dashboard overview
│   ├── components/            # Shared UI (Badge)
│   └── lib/                   # API client (axios), utilities
│
├── backend/                   # FastAPI + SQLAlchemy (async)
│   └── app/
│       ├── api/               # Route handlers (cases, dashboard, demo, webhooks)
│       ├── models/            # SQLAlchemy models (Customer, Payment, RecoveryCase, etc.)
│       ├── schemas/           # Pydantic schemas (PolicyDecision, RecoveryActionType)
│       ├── services/          # Business logic (AI Agent, Policy Engine, Recovery Engine)
│       ├── integrations/      # Razorpay client & webhook utilities
│       ├── db/                # Database session & engine config
│       └── config.py          # Settings from environment
│
├── scripts/                   # Test and utility scripts
├── docs/                      # Architecture, API, demo documentation
├── docker-compose.yml         # PostgreSQL container
└── .env.example               # Environment variable template
```

---

## 📜 API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check (DB connectivity) |
| `GET` | `/recovery-cases` | List all recovery cases |
| `GET` | `/recovery-cases/search?q=...` | Search cases by name, email, ID, status, amount, etc. |
| `GET` | `/recovery-cases/{id}` | Case detail with customer, payment, and audit logs |
| `POST` | `/recovery-cases/{id}/sync` | Sync payment link status from Razorpay |
| `GET` | `/dashboard/summary` | Dashboard metrics, funnel, and action distribution |
| `POST` | `/webhooks/razorpay` | Incoming Razorpay webhook handler |
| `POST` | `/demo/scenarios` | Trigger a demo scenario |
| `POST` | `/demo/scenarios/simulate-payment` | Simulate customer payment for a case |

---

## 📄 License

This project is for demonstration and educational purposes.
