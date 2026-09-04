<div align="center">

# RevivePay

**AI-powered revenue recovery for Razorpay merchants**

Failed payments aren't always final. RevivePay intercepts `payment.failed` webhooks in real time, uses AI to diagnose the root cause, enforces deterministic safety guardrails, and automatically executes recovery actions — then proves how much revenue was actually recovered.

**Razorpay Buildathon 2026 · AI Revenue Recovery Track**

---

[▶️ Watch the 5-Minute Demo](https://youtu.be/oMmOvdvVjFY) · [🚀 Quick Start](#-quick-start) · [📡 Local API Docs](http://localhost:8000/docs)

</div>

---

## 🎥 Demo

[**Watch the 5-Minute RevivePay Demo →**](https://youtu.be/oMmOvdvVjFY)

End-to-end payment failure detection, AI diagnosis, policy evaluation, recovery action, simulated customer payment, and recovered revenue — all demonstrated in a single walkthrough.

> [!NOTE]
> This is an unlisted YouTube video for Buildathon submission.

---

## Why RevivePay?

Most payment systems treat a failed transaction as a terminal event. The merchant eats the loss; the customer bounces.

RevivePay turns failed payments into recoverable revenue:

1. **Detect** — Razorpay `payment.failed` webhook arrives in real time.
2. **Diagnose** — AI (Google Gemini) classifies the failure and recommends a recovery action.
3. **Guard** — A deterministic Policy Engine evaluates whether the recommendation is safe to execute.
4. **Recover** — Approved actions are executed automatically (e.g., Razorpay Payment Link created).
5. **Verify** — When the customer pays, the loop closes and recovered revenue is recorded.

AI **recommends**. Deterministic policy **decides**. Every step is audited.

---

## 🔄 End-to-End Recovery Flow

```
Payment Failed
      ↓
Razorpay Webhook (payment.failed)
      ↓
Recovery Case Created
      ↓
AI Diagnosis (Gemini / Deterministic Fallback)
      ↓
Policy Guardrails (fraud · risk · amount · action)
      ↓
Recovery Action (Payment Link created)
      ↓
Customer Payment (via link)
      ↓
Revenue Recovered ✓
```

| Stage | What Happens |
|---|---|
| **Webhook** | `payment.failed` arrives, HMAC-SHA256 verified, idempotency checked |
| **Case Created** | Customer, Payment, and RecoveryCase records persisted |
| **AI Diagnosis** | Gemini (or deterministic fallback) classifies failure, estimates confidence, recommends action |
| **Policy Check** | Deterministic rules evaluate fraud, risk score, amount ceiling, action type |
| **Recovery Action** | If approved: Razorpay Payment Link created (real or simulated) |
| **Customer Payment** | Customer pays via the link; `payment_link.paid` webhook confirms |
| **Verification** | Recovered amount recorded, case status updated to `recovered` |

---

## 🛡️ AI Safety & Guardrails

RevivePay's strongest differentiator: **AI never acts alone.**

```
Gemini AI → Structured Diagnosis → Deterministic Policy Engine → Approved Action Only → Audit Trail
```

The AI produces a structured diagnosis (classification, confidence score, recommended action). A **deterministic Policy Engine** then independently decides whether that recommendation can be executed:

| Guardrail | Rule | Outcome |
|---|---|---|
| **Fraud Block** | Classification is `fraud` | `BLOCK` → Manual Review |
| **Recovery Threshold** | Confidence below `0.2` | `BLOCK` → Manual Review |
| **Amount Ceiling** | Amount exceeds ₹5,000 (500,000 paise) | `MANUAL_REVIEW` |
| **Action Restriction** | Only `create_payment_link` is auto-executable | All other actions → `MANUAL_REVIEW` |

**Outcomes:** `APPROVE`, `BLOCK`, or `MANUAL_REVIEW` — each logged with risk level, reason, and violated rule.

> [!IMPORTANT]
> AI is **advisory only**. The Policy Engine is fully deterministic — no LLM is in the execution path.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Docker & Docker Compose** (for PostgreSQL)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd Razorpay

# macOS / Linux / Git Bash
cp .env.example backend/.env

# Windows PowerShell
Copy-Item .env.example backend/.env
```
*(Then edit `backend/.env` with your values — see Environment Variables below)*

### 2. Start Database

```bash
docker-compose up -d
```
This starts PostgreSQL 16 on port **5433**.

### 3. Start Backend (Terminal 1)

The backend and frontend must run simultaneously in separate terminals.

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

### 5. Verify

| Service | URL |
|---|---|
| Frontend | [http://localhost:3000](http://localhost:3000) |
| Backend Health | [http://localhost:8000/health](http://localhost:8000/health) |
| API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## ⚙️ Environment Variables

The backend loads all configuration from **`backend/.env`** via [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). The frontend uses no environment variables (backend URL is hardcoded). Docker Compose uses hardcoded values and does not depend on any `.env` file.

```bash
# Setup:
cp .env.example backend/.env
# Then edit backend/.env with your values
```

See `.env.example` for the full template. **Never commit `backend/.env` to version control.**

| Variable | Required | Description |
|---|---|---|
| `RAZORPAY_WEBHOOK_SECRET` | Yes | HMAC secret for webhook signature verification |
| `DATABASE_URL` | Optional | PostgreSQL async connection string (defaults to docker-compose setup) |
| `DATABASE_URL_SYNC` | Optional | PostgreSQL sync connection string (defaults to docker-compose setup) |
| `RAZORPAY_KEY_ID` | Optional | Enables real Razorpay Test Mode payment links |
| `RAZORPAY_KEY_SECRET` | Optional | Razorpay API secret for Test Mode |
| `AI_PROVIDER` | Optional | `gemini` or `openai` (default: `gemini`) |
| `GEMINI_API_KEY` | Optional | Enables AI diagnosis via Google Gemini |
| `GEMINI_MODEL` | Optional | Gemini model (default: `gemini-3.6-flash`) |
| `OPENAI_API_KEY` | Optional | Enables AI diagnosis via OpenAI |
| `OPENAI_MODEL` | Optional | OpenAI model (default: `gpt-4o-mini`) |
| `APP_MODE` | Optional | `developer` for simulated/fallback mode (default: `developer`) |
| `APP_ENV` | Optional | Environment name (default: `development`) |
| `APP_DEBUG` | Optional | Enable debug logging (default: `true`) |
| `BACKEND_URL` | Optional | Backend self-URL for demo webhooks (default: `http://localhost:8000`) |
| `FRONTEND_URL` | Optional | CORS origin (default: `http://localhost:3000`) |

> [!TIP]
> **Minimal setup (Demo Mode):** Only `RAZORPAY_WEBHOOK_SECRET` is strictly required. `DATABASE_URL` and `DATABASE_URL_SYNC` have working defaults that match the Docker container.
>
> In the default Developer Mode, RevivePay can run the full recovery pipeline using deterministic fallback diagnosis and simulated payment links. Live Gemini diagnosis requires a Gemini API key and provider configuration. Real Razorpay Test Mode payment links require Razorpay credentials and the corresponding runtime configuration.

---

## 🎮 Run the End-to-End Demo

This is the fastest way to see RevivePay in action. **~2 minutes.**

> [!NOTE]
> For a fresh clone, run `alembic upgrade head` once during backend setup to initialize/update the database schema.

| Step | Action |
|---|---|
| 1 | Start PostgreSQL: `docker-compose up -d` |
| 2 | Start backend: `cd backend && uvicorn app.main:app --reload --port 8000` |
| 3 | Start frontend: `cd frontend && npm run dev` |
| 4 | Open [http://localhost:3000](http://localhost:3000) — the Dashboard |
| 5 | Click **Demo Control** in the sidebar (or navigate to [/demo](http://localhost:3000/demo)) |
| 6 | Click **"Successful Recovery"** scenario |
| 7 | Navigate to **Recovery Cases** in the sidebar |
| 8 | Click the newly created case to open the **Case Detail** page |
| 9 | Review the **AI Diagnosis** (classification, confidence, recommended action) |
| 10 | Review the **Policy Decision** (outcome, risk level, reason) |
| 11 | See the generated **Payment Link** (simulated in Developer Mode) |
| 12 | Click **"Simulate Customer Payment"** to simulate the customer paying |
| 13 | Return to the **Dashboard** ([/](http://localhost:3000)) and verify **Revenue Recovered** has increased |

> [!TIP]
> Try the other scenarios too — **Guardrail Block** shows fraud detection, **Duplicate Webhook** proves idempotency.

---

## 🎬 Demo Mode

### Why It Exists

Demonstrating a webhook-driven payment flow normally requires exposing your local server to the internet (via Ngrok or similar). Demo Mode eliminates this requirement by generating synthetic Razorpay webhook payloads locally.

### How It Works

1. The Demo Control panel sends a request to `POST /demo/scenarios`.
2. The backend constructs a synthetic `payment.failed` webhook payload.
3. The payload is **HMAC-SHA256 signed** using the local `RAZORPAY_WEBHOOK_SECRET`.
4. The signed payload is sent to the **same `/webhooks/razorpay` endpoint** that handles real Razorpay webhooks.
5. The webhook handler processes it through the **identical pipeline** — signature verification, idempotency check, case creation, AI diagnosis, policy evaluation, and action execution.

### Available Scenarios

| # | Scenario | What It Demonstrates |
|---|---|---|
| 1 | **Successful Recovery** | Full happy path: fail → diagnose → approve → payment link → recover |
| 2 | **Payment Link Recovery** | `INSUFFICIENT_FUNDS` failure; customer-action-needed flow |
| 3 | **Guardrail Block** | Fraud classification; policy engine blocks and routes to manual review |
| 4 | **Execution Failure** | Simulated upstream API timeout; graceful failure handling |
| 5 | **Duplicate Webhook** | Same `payment.failed` sent twice; validates idempotency |

### Real vs. Simulated

| Component | Real | Simulated in Demo Mode |
|---|---|---|
| Webhook pipeline | ✅ Full processing | ✅ Full processing (synthetic payload) |
| HMAC verification | ✅ Real HMAC-SHA256 | ✅ Real HMAC-SHA256 (local secret) |
| AI Diagnosis | ✅ When API key configured | ✅ Deterministic fallback |
| Policy Engine | ✅ Always deterministic | ✅ Always deterministic |
| Payment Links | ✅ Real Razorpay Test Mode | Simulated link (no Razorpay API call) |
| Customer Payment | ✅ Via `payment_link.paid` webhook | Simulated via "Simulate Payment" button |

---

## 📸 Product Preview

<!-- 
Screenshots are not yet added to the repository.
To add them, place images in docs/images/ and uncomment the lines below.

![Dashboard Overview](docs/images/dashboard.png)
![Case Detail — AI Diagnosis & Policy Decision](docs/images/case-detail.png)
![Demo Control Panel](docs/images/demo-control.png)
![Recovered Revenue](docs/images/recovered.png)
-->

> [!NOTE]
> Screenshots are pending. See the [5-Minute Demo video](https://youtu.be/oMmOvdvVjFY) for a full visual walkthrough.

---

## ✨ Key Features

### 🤖 AI-Powered Diagnosis
- **Gemini / OpenAI Integration** — Structured diagnosis via Google Gemini (`gemini-3.6-flash`) or OpenAI (`gpt-4o-mini`), selected by `AI_PROVIDER` config.
- **Structured Output** — AI returns a Pydantic-validated schema: `classification`, `confidence`, `recommended_action`, `reason`.
- **Deterministic Fallback** — When no API key is configured, the AI call fails, or `APP_MODE=developer`, a rule-based engine maps error codes to classifications and actions. The pipeline never stalls.
- **Decision Source Tagging** — Every diagnosis is tagged `ai_agent` or `system_fallback` so operators always know which engine made the call.

### 🛡️ Policy Engine
- Fraud block, recovery score threshold (`0.2`), amount ceiling (₹5,000), action restrictions.
- Outcomes: `APPROVE`, `BLOCK`, `MANUAL_REVIEW` — each with risk level, reason, and violated rule.
- Fully deterministic — no LLM in the decision path.

### ⚡ Automated Recovery
- **Payment Link Creation** — Real Razorpay Test Mode links (when credentials are configured) or simulated links (Developer Mode).
- **Recovery Verification** — `payment_link.paid` webhook or manual sync confirms payment and updates case status to `recovered` / `partially_recovered`.

### 🔗 Razorpay Webhooks
- HMAC-SHA256 signature verification on every webhook.
- `X-Razorpay-Event-Id` idempotency — duplicates are detected and safely ignored.
- Supported events: `payment.failed`, `payment_link.paid`, `payment.captured`.

### 📊 Dashboard
- Revenue metrics: At Risk, Recoverable, Attempted, Recovered.
- Recovery Rate with visual progress bar.
- Recovery Funnel (horizontal bar chart) and Action Distribution (donut chart).
- Recent Cases with status badges. System Status footer.

### 🔍 Global Search
- Command palette triggered by `⌘K` / `Ctrl+K`.
- Searches across customer name, email, payment ID, status, failure reason/code, action, case ID, and amount.
- 300ms debounce, keyboard navigation, click-to-navigate.

### 📋 Recovery Cases
- Live polling (5-second refresh). Color-coded status badges.
- Tabular view with customer info, amount, failure details, actions, and recovery data.

### 📄 Case Details
- Visual progress tracker: Payment Failed → Case Created → AI Diagnosis → Policy Check → Recovery Action → Verification.
- AI Diagnosis card with classification, confidence bar, recommended action, and decision source.
- Policy Decision card with outcome, risk level, reason, and violated rule.
- Recovery Action card with mode indicator (Real Test Mode vs. Simulated Demo).
- **Simulate Payment** button (Developer Mode) and **Sync Payment Status** button (Real Test Mode).
- Full audit timeline with collapsible raw JSON.

### 🎮 Demo Control
- Five pre-built scenarios (see [Demo Mode](#-demo-mode)).

### 🌗 Dark / Light Theme
- Persistent preference in `localStorage`.
- Light: cloud/sky gradient with glassmorphism cards. Dark: night background with starfield particles.
- Smooth 500ms CSS transitions.

---

## 🔗 Razorpay Integration

### Webhook Events

| Event | Handler |
|---|---|
| `payment.failed` | Creates recovery case, triggers full pipeline |
| `payment_link.paid` | Verifies recovery, updates case to `recovered` |
| `payment.captured` | Acknowledged and logged, not processed |

### Security

- **HMAC-SHA256 Verification** — Every webhook signature is verified using `RAZORPAY_WEBHOOK_SECRET` via `hmac.compare_digest` (timing-attack safe).
- **Idempotency** — `X-Razorpay-Event-Id` is stored in `WebhookEvent` table; duplicate events are ignored.

### Payment Link API

- **Real Test Mode** — When `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are set, the system calls `POST /v1/payment_links/` on the Razorpay API (Basic Auth). Real test-mode links are created and can be paid.
- **Simulated Developer Mode** — When Razorpay credentials are absent (or `APP_MODE=developer`), a simulated link ID is generated (`plink_sim_...`) so the full pipeline can be demonstrated without API credentials.

### Sync

`POST /recovery-cases/{id}/sync` fetches the latest payment link status from Razorpay and triggers recovery verification if the link has been paid.

---

## 🤖 AI Architecture

### Provider Support

RevivePay supports two AI providers, selected via the `AI_PROVIDER` environment variable:

| Provider | SDK | Default Model | Structured Output Method |
|---|---|---|---|
| **Google Gemini** (primary) | `google-genai` | `gemini-3.6-flash` | `response_schema` with JSON MIME type |
| **OpenAI** (alternative) | `openai` | `gpt-4o-mini` | `beta.chat.completions.parse` |

Both providers are fully implemented and can be switched at runtime via `AI_PROVIDER=gemini` or `AI_PROVIDER=openai` in `backend/.env`.

> [!NOTE]
> The model name is configurable via `GEMINI_MODEL` or `OPENAI_MODEL` in `backend/.env`. The defaults shown above are from `config.py`.

### Structured Diagnosis Output

```python
class AIDiagnosisResult(BaseModel):
    classification: str     # e.g. "temporary_failure", "insufficient_funds", "fraud"
    confidence: float       # 0.0 – 1.0
    recommended_action: RecoveryActionType  # "create_payment_link" | "manual_review"
    reason: str             # Concise explanation
```

### Deterministic Fallback

When no API key is configured, the key is empty, or `APP_MODE=developer`:
- A rule-based engine maps Razorpay error codes (e.g., `GATEWAY_ERROR`, `FRAUD`) to classifications and recommended actions.
- Every diagnosis made by the fallback is tagged as `system_fallback` in the UI and audit log.

### Decision Source Tagging

The UI clearly labels each diagnosis with its source:
- **AI Agent** — Diagnosis came from Gemini or OpenAI.
- **System Fallback** — Diagnosis came from the deterministic rule-based engine.

---

## 🏗️ Architecture

```
Next.js Frontend (TypeScript + Tailwind CSS)
        ↕ REST API (axios)
FastAPI Backend (Python 3.12+)
        ├── Webhook Handler        → Signature verification, idempotency, event routing
        ├── AI Agent Service       → Gemini / OpenAI / Deterministic Fallback
        ├── Policy Engine          → Deterministic guardrails (fraud, risk, amount, action)
        ├── Recovery Engine        → Orchestrates diagnosis → policy → execution → verification
        └── Action Executor        → Razorpay Payment Link API / Simulated links
              ↓
        Razorpay API (Test Mode)
              ↓
        PostgreSQL (SQLAlchemy async + Alembic)
```

- **Frontend** — Next.js app with dashboard, case management, global search, demo control, and theme switching. Communicates with the backend via REST.
- **Backend** — FastAPI application orchestrating the recovery pipeline. Each stage (diagnosis, policy, execution, verification) is a separate service with clear boundaries.
- **Database** — PostgreSQL with async SQLAlchemy. Alembic manages migrations.
- **Integrations** — Razorpay API client (httpx-based, Basic Auth) and webhook signature verification utilities.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Next.js 16** | Frontend framework |
| **React 19** | UI library |
| **TypeScript** | Frontend type safety |
| **Tailwind CSS 4** | Styling |
| **Recharts** | Dashboard charts (funnel, donut) |
| **Lucide React** | Icons |
| **FastAPI** | Backend framework |
| **Python 3.12+** | Backend language |
| **SQLAlchemy (async)** | ORM |
| **Alembic** | Database migrations |
| **PostgreSQL 16** | Persistence |
| **Google Gemini** | AI diagnosis (via `google-genai` SDK) |
| **OpenAI** | AI diagnosis (alternative provider) |
| **Razorpay API** | Payment links, webhook verification |
| **httpx** | Async HTTP client (backend) |
| **axios** | HTTP client (frontend) |
| **Docker Compose** | PostgreSQL container |

---

## 🗄️ Database Models

| Model | Purpose |
|---|---|
| `Customer` | Customer info (name, email, phone) |
| `Payment` | Razorpay payment details (amount, currency, failure code/reason) |
| `RecoveryCase` | Core entity: links a failed payment to its recovery journey |
| `RecoveryAction` | Records executed actions (type, provider ID, result, status) |
| `AuditLog` | Immutable timeline events with structured metadata JSON |
| `WebhookEvent` | Raw webhook payloads for idempotency checks |

---

## 📁 Project Structure

```
├── frontend/                  # Next.js + TypeScript + Tailwind CSS
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
│   ├── app/
│   │   ├── api/               # Route handlers (cases, dashboard, demo, webhooks)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas (AIDiagnosisResult, PolicyDecision, etc.)
│   │   ├── services/          # AI Agent, Policy Engine, Recovery Engine, Action Executor
│   │   ├── integrations/      # Razorpay client & webhook utilities
│   │   ├── db/                # Database session & engine config
│   │   └── config.py          # Settings from environment
│   ├── scripts/               # Test and utility scripts
│   └── alembic/               # Database migrations
│
├── docs/                      # Architecture, API, demo documentation
├── docker-compose.yml         # PostgreSQL 16 container (port 5433)
└── .env.example               # Environment variable template
```

---

## ✅ Implementation Status

| Feature | Status | Notes |
|---|---|---|
| Razorpay `payment.failed` Webhook | ✅ Working | HMAC-SHA256 verified, idempotent |
| Razorpay `payment_link.paid` Webhook | ✅ Working | Triggers recovery verification |
| AI Diagnosis (Gemini) | ✅ Working | Structured output via `google-genai` SDK |
| AI Diagnosis (OpenAI) | ✅ Working | Structured output via `openai` SDK |
| Deterministic Fallback | ✅ Working | Rule-based, always available |
| Policy Engine | ✅ Working | Fully deterministic, 4 guardrail rules |
| Payment Links (Real Test Mode) | ✅ Working | Requires Razorpay credentials |
| Payment Links (Simulated) | ✅ Working | Developer Mode, no credentials needed |
| Recovery Verification | ✅ Working | Via webhook or manual sync |
| Demo Simulator | ✅ Working | 5 scenarios, synthetic HMAC-signed webhooks |
| Dashboard & Charts | ✅ Working | Revenue metrics, funnel, action distribution |
| Global Search | ✅ Working | Multi-field search with keyboard navigation |
| Dark / Light Theme | ✅ Working | Persistent, animated transitions |

---

## 📡 API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check (DB connectivity) |
| `GET` | `/recovery-cases` | List all recovery cases |
| `GET` | `/recovery-cases/search?q=...` | Search cases across multiple fields |
| `GET` | `/recovery-cases/{id}` | Case detail with customer, payment, audit logs |
| `POST` | `/recovery-cases/{id}/sync` | Sync payment link status from Razorpay |
| `GET` | `/dashboard/summary` | Dashboard metrics, funnel, action distribution |
| `POST` | `/webhooks/razorpay` | Incoming Razorpay webhook handler |
| `POST` | `/demo/scenarios` | Trigger a demo scenario |
| `POST` | `/demo/scenarios/simulate-payment` | Simulate customer payment for a case |

Full interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) when the backend is running.

---

## 🧪 Testing

```bash
cd backend
python -m scripts.test_webhook
```

The test script validates the webhook processing pipeline, idempotency handling, and core recovery flow.

> [!NOTE]
> AI API keys are intentionally disabled during testing to ensure the deterministic fallback and policy engine function correctly without external dependencies.

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| **PostgreSQL connection refused** | Ensure Docker is running: `docker-compose up -d`. Check that port 5433 is not in use. |
| **Backend won't start** | Verify Python 3.12+. Install deps: `pip install -r requirements.txt`. Ensure PostgreSQL is running and, if `DATABASE_URL` is explicitly configured, verify that it points to the correct database. |
| **Frontend can't reach backend** | Ensure backend is running on port 8000. The frontend API URL is hardcoded to `http://localhost:8000`. |
| **"Webhook secret not configured"** | Set `RAZORPAY_WEBHOOK_SECRET` in `backend/.env`. Any string works for Demo Mode. |
| **AI diagnosis returns `system_fallback`** | Expected when `GEMINI_API_KEY` / `OPENAI_API_KEY` is missing or `APP_MODE=developer`. The fallback is fully functional. |
| **Payment link shows "Simulated"** | Expected in Developer Mode (`APP_MODE=developer` or no Razorpay credentials). Set `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and change `APP_MODE` in `backend/.env` to use real Test Mode links. |
| **Demo scenario does nothing** | Check backend logs. Ensure `RAZORPAY_WEBHOOK_SECRET` is set in `backend/.env` (the demo signs payloads with this secret). |

---

## 🧩 What Broke & How We Solved It

### 1. LLM Reliability — Hallucinated & Invalid Actions

**Problem:** Early iterations let the LLM return free-text action recommendations. It would hallucinate non-existent actions, return malformed JSON, or recommend actions the system couldn't execute.

**Solution:**
- Constrained AI output to a **Pydantic schema** (`AIDiagnosisResult`) with a fixed `RecoveryActionType` enum (`create_payment_link`, `manual_review`).
- Used **structured output** APIs (Gemini `response_schema`, OpenAI `beta.chat.completions.parse`) to enforce schema compliance at the model level.
- Added a **deterministic Policy Engine** as a hard gate — even if the AI recommends an action, the policy engine independently decides whether it's safe.
- Built a **deterministic fallback** that maps error codes to classifications, ensuring the pipeline never depends on LLM availability.

### 2. Demonstrating Webhook-Driven Flows

**Problem:** Razorpay webhooks require a publicly accessible endpoint. During development and demos, this means setting up Ngrok/tunnels — fragile, slow, and distracting for judges.

**Solution:**
- Built a **local Demo Simulator** that constructs synthetic Razorpay webhook payloads.
- Payloads are **HMAC-SHA256 signed** using the same local webhook secret.
- Signed payloads are sent to the **same `/webhooks/razorpay` endpoint** — processed through the identical pipeline (signature verification, idempotency, case creation, recovery).
- Five pre-built scenarios cover happy paths, guardrail blocks, execution failures, and idempotency validation.

---

## 🔐 Security

- **Never commit `backend/.env`** — it contains real credentials. Both `.env` and `backend/.env` are listed in `.gitignore`.
- **Use `.env.example` as a template** — copy it to `backend/.env` and fill in your values. `.env.example` contains no real secrets and is safe to commit.
- **Credentials are optional for demos** — `APP_MODE=developer` (the default) enables the deterministic fallback and simulated payment links, so the full pipeline can be demonstrated without Razorpay or AI credentials.
- **Real credentials are needed only for** real Razorpay Test Mode payment links (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) and live AI diagnosis (`GEMINI_API_KEY` or `OPENAI_API_KEY`).

---

## 📄 License

This project is for demonstration and educational purposes.
