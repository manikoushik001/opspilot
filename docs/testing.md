# OpsPilot Testing Strategy & Verification Report

OpsPilot maintains an extensive automated testing suite covering unit tests, security and cross-tenant boundaries, RAG pipeline scenarios, and AI evaluation metrics.

---

## 1. Test Suite Structure (`backend/app/tests/`)

| Test Module | Coverage Area | Key Assertions |
|---|---|---|
| `test_auth.py` | Registration, Login, Token Refresh, Inactive User | Registration creates user and default business membership with OWNER role. Invalid passwords return 401. Duplicate emails return 400. |
| `test_tenant_isolation.py` | Cross-Tenant Security | Tenant A user cannot read, update, or delete Tenant B customer (returns 404). Spoofed `X-Business-ID` header rejected with 403. Vector search for Tenant A returns zero chunks from Tenant B. |
| `test_customers.py` | Customer CRUD, Search, Pagination | Full lifecycle of customer creation, field updates, keyword search, and deletion. |
| `test_conversations.py` | Conversation Lifecycle & Simulated Influx | Opening conversation, staff response creation, simulated customer message processing, and status transition to `RESOLVED`. |
| `test_rag.py` | Grounded RAG Scenarios 1–6 | Fee inquiry groundings, non-existent course escalation (no hallucination), refund request routing, follow-up suggestion & execution, prompt injection rejection. |
| `test_followups.py` | Task Scheduling & Overdue Calculation | Task creation, status updates, overdue flag computation, and completion timestamps. |
| `test_analytics.py` | Operational Metrics Aggregation | Customer counts, resolution method breakdowns, daily volume trends, and average confidence computations. |
| `test_security.py` | RBAC & Token Enforcement | Unauthenticated `/health` passes; invalid JWTs return 401; Staff members attempting Owner-only actions return 403 Forbidden. |

---

## 2. Test Execution Commands

### Backend Pytest Suite
```bash
cd backend
python -m pytest -v app/tests
```
**Result**: `17 passed in 7.37s` (100% pass rate).

### AI Evaluation Suite
```bash
python evaluation/run_eval.py
```
**Result**: Evaluated across 9 structured cases covering ANSWERABLE, UNANSWERABLE, AMBIGUOUS, SENSITIVE, PROMPT_INJECTION, and HALLUCINATION_TRAP. Intent accuracy: 100%, Escalation accuracy: 88.9%.

### Frontend Next.js Production Build
```bash
cd frontend
npm run build
```
**Result**: Successfully compiled 13/13 routes (`/`, `/login`, `/register`, `/dashboard`, `/conversations`, `/customers`, `/knowledge`, `/followups`, `/analytics`, `/settings`) with zero TypeScript or build errors.
