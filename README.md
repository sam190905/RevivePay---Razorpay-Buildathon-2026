# RevivePay

AI-powered revenue recovery system for Razorpay. Detects failed payments, diagnoses failure causes, estimates recovery probability, recommends actions within deterministic guardrails, and executes recovery — proving how much revenue was actually recovered.

## Architecture

```
Next.js Frontend → FastAPI Backend → PostgreSQL
                                   → AI Service (OpenAI-compatible)
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

## Project Structure

```
├── frontend/          # Next.js + TypeScript + Tailwind
├── backend/           # FastAPI + SQLAlchemy
│   └── app/
│       ├── api/           # Route handlers
│       ├── models/        # SQLAlchemy models
│       ├── schemas/       # Pydantic schemas
│       ├── services/      # Business logic
│       ├── agents/        # AI recovery agent
│       ├── policies/      # Deterministic guardrails
│       ├── actions/       # Recovery action executors
│       ├── integrations/  # Razorpay client
│       ├── db/            # Database config
│       └── utils/         # Helpers
├── scripts/           # Seed data, utilities
├── docs/              # Architecture, API, demo docs
└── docker-compose.yml # PostgreSQL
```
