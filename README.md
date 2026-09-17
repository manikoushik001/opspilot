# OpsPilot

> **AI-powered customer operations platform for service businesses.**  
> A multi-tenant SaaS application featuring grounded RAG, human escalation workflows, and schema-validated AI actions built with FastAPI, PostgreSQL + pgvector, Redis, Celery, and Next.js 14.

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

## 🔑 Demo Credentials (Fictional Demo Accounts)

OpsPilot includes a pre-seeded fictional demo organization: **"Demo Learning Center"** (for local testing & demonstration only).

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Business Owner** | `owner@demolearning.com` | `password123` | Full administrative access: Settings, Knowledge Base, Analytics, Customers, Audit Logs |
| **Operations Staff** | `staff@demolearning.com` | `password123` | Operational access: Conversations inbox, Customer management, Follow-up tasks |

---

## 🧪 Automated Testing & Evaluation

### Run Backend Pytest Suite
```bash
cd backend
python -m pytest -v app/tests
```
**Results**: `29 passed` (100% pass rate) covering JWT lifecycle, refresh token rotation, RBAC, cross-tenant isolation, path traversal defense, customer CRUD, conversation lifecycle, grounded RAG retrieval, AI action proposal validation, prompt injection defense, follow-ups, and analytics.

### Run AI & RAG Evaluation Suite
```bash
python evaluation/run_eval.py
```
**Results**: `9/9 benchmark cases passed` (100.0% Intent Accuracy, 100.0% Escalation Accuracy, 100.0% Grounding Match) across Answerable, Unanswerable, Ambiguous, Sensitive, Prompt Injection, and Hallucination Trap scenarios.

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
