# OpsPilot

> **AI-powered customer operations for small businesses.**  
> A serious, portfolio-quality, multi-tenant SaaS application built with Python FastAPI, PostgreSQL + pgvector, Redis, Celery, and Next.js 14.

---

## 🌟 Product Overview

Small service businesses (such as vocational centers, tutoring academies, and learning institutes) struggle with fragmented customer communication, repetitive inquiries, forgotten follow-ups, and lack of operational visibility.

**OpsPilot** centralizes customer operations into a single, secure, multi-tenant workspace where:
1. **AI Proposes, Application Validates**: AI never has direct database access. Proposed actions (e.g. follow-up creation, status changes) pass through schema validation, authorization, and business rules before execution.
2. **Grounded RAG Answers**: Responses are synthesized strictly from tenant-approved knowledge documents indexed in PostgreSQL with `pgvector`.
3. **Automated Human Escalation**: Low confidence, ambiguous policies, refund requests, customer complaints, and prompt injection attacks automatically transition conversations to `HUMAN_REVIEW`.
4. **Follow-up Management**: Scheduled check-ins with automated overdue detection.
5. **Operational Analytics & Auditing**: Real-time resolution breakdown, response times, intent distribution, and a redacted audit trail.

---

## 🚀 Quickstart

### Option 1: Docker Compose (Recommended)

```bash
# Clone and spin up full stack (PostgreSQL + pgvector, Redis, Celery worker, FastAPI backend, Next.js frontend)
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/api/v1/docs`
- Health Check: `http://localhost:8000/health`

---

### Option 2: Local Manual Setup

#### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Run full Pytest suite
python -m pytest -v app/tests

# Run local development server
uvicorn app.main:app --reload --port 8000
```

#### 2. Seed Demo Data (Demo Learning Center)
```bash
# From workspace root
python scripts/seed_data.py
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🔑 Demo Credentials (Fictional Demo Data)

OpsPilot includes a pre-seeded fictional demo organization: **"Demo Learning Center"**.

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Business Owner** | `owner@demolearning.com` | `password123` | Full access: Settings, Knowledge Base, Analytics, Customers, Audit Logs |
| **Operations Staff** | `staff@demolearning.com` | `password123` | Operational access: Conversations, Customer inbox, Follow-up tasks |

---

## 🧪 Automated Testing & Evaluation

### Run Backend Pytest Suite
```bash
cd backend
python -m pytest -v app/tests
```
**Results**: 17 passed (100% pass rate) covering auth, cross-tenant isolation, customer CRUD, conversation lifecycle, RAG scenarios 1–6, follow-ups, analytics, and security.

### Run AI & RAG Evaluation Suite
```bash
python evaluation/run_eval.py
```
**Results**: Evaluates golden test dataset across 7 categories (Answerable, Unanswerable, Ambiguous, Sensitive, Prompt Injection, Conflicting Info, Hallucination Trap).

### Run Frontend Production Build
```bash
cd frontend
npm run build
```
**Results**: Compiles 13/13 routes with zero TypeScript or linting errors.

---

## 📚 Comprehensive Documentation Suite

- [ARCHITECTURE.md](ARCHITECTURE.md): System architecture, Mermaid diagrams, component breakdown, security model.
- [PROJECT_LOG.md](PROJECT_LOG.md): Engineering decisions, tradeoffs, and outcomes log.
- [FINAL_VERIFICATION_REPORT.md](FINAL_VERIFICATION_REPORT.md): Comprehensive test, security, and verification report.
- [docs/DATA_FLOW.md](docs/DATA_FLOW.md): Complete data lifecycle and authorization flow diagrams.
- [docs/FILE_MAP.md](docs/FILE_MAP.md): Detailed map and responsibility of every file in the repository.
- [docs/FAILURE_MODES.md](docs/FAILURE_MODES.md): Failure modes, detection, handling, user experience, and recovery paths.
- [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md): Developer guide explaining WHAT exists and WHY it was built.
- [docs/INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md): High-signal technical interview questions based strictly on the implementation.
- [docs/FINAL_BUILD_REPORT.md](docs/FINAL_BUILD_REPORT.md): Build verification and test report.
- [docs/problem-discovery.md](docs/problem-discovery.md): Domain discovery and user pain points.
- [docs/product-decisions.md](docs/product-decisions.md): Core architectural and product decisions.
- [docs/ai-engineering.md](docs/ai-engineering.md): Grounded RAG, intent classification, and safety systems.
- [docs/security.md](docs/security.md): Security architecture, JWT lifecycle, and RBAC policies.
- [docs/testing.md](docs/testing.md): Test strategy and test execution reports.
