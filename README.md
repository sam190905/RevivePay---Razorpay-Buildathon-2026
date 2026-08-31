# RevivePay

AI-powered revenue recovery system for Razorpay. Detects failed payments, diagnoses failure causes, estimates recovery probability, recommends actions within deterministic guardrails, and executes recovery — proving how much revenue was actually recovered.

## Architecture

```
Next.js Frontend → FastAPI Backend → PostgreSQL
                                   → AI Service (OpenAI-compatible) or Deterministic Fallback
                                   → Razorpay Test Mode API
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (for PostgreSQL)

### 1. Clone & Configure

```bash
cp .env.example .env
# Edit .env with your credentials
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

- Backend health: http://localhost:8000/health
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Environment Variables

See `.env.example` for all required configuration.

## Demo Scenarios

We have built a deterministic `/api/demo/scenarios` endpoint that fires synthetic webhooks. It simulates 5 core cases:
1. **Successful Recovery** (Basic retry via payment link)
2. **Payment Link Recovery** (Happy path through insufficient funds)
3. **Guardrail Block** (AI blocked by deterministic policy due to high risk)
4. **Execution Failure** (Simulated Razorpay downtime)
5. **Duplicate Webhook** (Idempotency check validation)

## Testing

Backend test suite ensures stability and idempotency:
```bash
cd backend
python -m scripts.test_webhook
```
*Note: We disable OpenAI API keys during regression testing to ensure the deterministic fallback and core policies function correctly.*

## Project Structure

```
├── frontend/          # Next.js + TypeScript + Tailwind
├── backend/           # FastAPI + SQLAlchemy
│   └── app/
│       ├── api/           # Route handlers
│       ├── models/        # SQLAlchemy models
│       ├── schemas/       # Pydantic schemas
│       ├── services/      # Business logic (AI Agent, Policy Engine, Recovery Engine)
│       ├── integrations/  # Razorpay client
│       └── db/            # Database config
├── scripts/           # Test and utility scripts
├── docs/              # Architecture, API, demo docs
└── docker-compose.yml # PostgreSQL
```
