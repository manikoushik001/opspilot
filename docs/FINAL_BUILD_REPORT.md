# OpsPilot Engineering Build & Verification Report

**Project**: OpsPilot - AI-Powered Customer Operations SaaS  
**Repository State**: Implemented, Tested, Seeded, and Verified  
**Build Status**: All Tests Passing (29/29), AI Eval Passed (9/9), Frontend Compiled (13/13 routes)

---

## 1. Executive Summary & Features Completed

OpsPilot is a multi-tenant SaaS application demonstrating backend, frontend, database, AI/RAG, security, and systems engineering:

- **Authentication & RBAC**: Registration, login, token refresh, password hashing with bcrypt, JWT authorization, and `OWNER` / `STAFF` roles.
- **Strict Multi-Tenancy**: Guaranteed tenant boundary isolation via dependency injection on every database query and API endpoint.
- **Customer Management**: Paginated directory, search, status filters, profile editor, and conversation/task associations.
- **Conversation Management**: Multi-channel inbox with status tracking (`OPEN`, `WAITING`, `HUMAN_REVIEW`, `RESOLVED`, `CLOSED`), staff responses, and simulated customer message intake.
- **Grounded RAG Pipeline**: Ingestion for PDF, Markdown, and TXT files; paragraph-aware semantic chunking; 1536-dim vector embeddings; tenant-isolated cosine similarity search.
- **Safe AI Decision Engine**: Intent classification (8 intents), grounding validation, prompt injection defense, and automated human-in-the-loop escalation.
- **Controlled Action System**: "AI proposes, Application validates, Business rules decide, System executes" workflow for `CREATE_FOLLOWUP`, `ESCALATE_TO_HUMAN`, and `UPDATE_CUSTOMER_STATUS`.
- **Follow-up Task Tracker**: Tabbed interface (Pending, Overdue, Completed) with automated overdue detection.
- **Analytics Dashboard**: Real-time metrics for resolution rate, response times, volume trends, and intent distributions.
- **Redacted Audit Logging**: Tamper-resistant audit trail with automatic redaction of sensitive credentials.
- **Pluggable AI Providers**: Full support for Mock (deterministic offline evaluation), OpenAI, Gemini, and Ollama.

---

## 2. Actual Technology Stack

| Layer | Technologies Used |
|---|---|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, Pydantic-Settings, Uvicorn |
| **Database & ORM** | PostgreSQL 16 + pgvector, SQLAlchemy 2.0 (Async/Sync), Alembic, aiosqlite |
| **Task Queue & Cache** | Redis 7, Celery 5.3+ |
| **Security & Auth** | PyJWT, bcrypt, python-multipart |
| **Document Processing** | pypdf, aiofiles |
| **Testing & QA** | Pytest, pytest-asyncio, pytest-mock, httpx |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, TanStack Query, Lucide Icons |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions (`.github/workflows/ci.yml`) |

---

## 3. Database Schema Overview

```
users (id, email, hashed_password, full_name, is_active, is_superuser, timestamps)
businesses (id, name, description, industry, email, phone, timezone, timestamps)
business_members (id, business_id, user_id, role [OWNER, STAFF], timestamps)
customers (id, business_id, name, email, phone, status [NEW, ACTIVE, FOLLOW_UP, RESOLVED, INACTIVE], notes, timestamps)
conversations (id, business_id, customer_id, status [OPEN, WAITING, HUMAN_REVIEW, RESOLVED, CLOSED], priority, assigned_to, resolved_at, timestamps)
messages (id, conversation_id, sender_type [CUSTOMER, STAFF, AI], sender_id, content, intent, ai_confidence, timestamps)
knowledge_documents (id, business_id, filename, mime_type, storage_path, status [UPLOADED, PROCESSING, READY, FAILED], chunk_count, error_message, timestamps)
knowledge_chunks (id, business_id, document_id, chunk_index, content, embedding_json, meta_json, timestamps)
followups (id, business_id, customer_id, conversation_id, assigned_to, title, description, due_at, status [PENDING, COMPLETED, CANCELLED], completed_at, timestamps)
ai_interactions (id, business_id, conversation_id, message_id, model, operation, confidence, retrieval_count, latency_ms, success, timestamps)
ai_actions (id, business_id, conversation_id, action_type, status [PROPOSED, VALIDATED, EXECUTED, REJECTED], reason, payload_json, execution_result, timestamps)
audit_logs (id, business_id, user_id, action, resource_type, resource_id, metadata_json, timestamps)
```

---

## 4. API Endpoints Implemented

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/business` & `PATCH /api/v1/business`
- `GET /api/v1/customers` & `POST /api/v1/customers`
- `GET /api/v1/customers/{id}`, `PATCH /api/v1/customers/{id}`, `DELETE /api/v1/customers/{id}`
- `GET /api/v1/conversations` & `POST /api/v1/conversations`
- `GET /api/v1/conversations/{id}` & `PATCH /api/v1/conversations/{id}`
- `GET /api/v1/conversations/{id}/messages` & `POST /api/v1/conversations/{id}/messages`
- `POST /api/v1/conversations/{id}/simulate-customer`
- `GET /api/v1/knowledge/documents` & `POST /api/v1/knowledge/documents`
- `GET /api/v1/knowledge/documents/{id}/chunks`
- `DELETE /api/v1/knowledge/documents/{id}`
- `POST /api/v1/knowledge/search`
- `GET /api/v1/followups` & `POST /api/v1/followups`
- `GET /api/v1/followups/{id}` & `PATCH /api/v1/followups/{id}`
- `POST /api/v1/ai/classify`
- `POST /api/v1/ai/answer`
- `POST /api/v1/ai/suggest-action`
- `POST /api/v1/ai/execute-action`
- `GET /api/v1/analytics/overview`
- `GET /api/v1/audit-logs`
- `GET /health` & `GET /`

---

## 5. Automated Verification Results

### 1. Backend Pytest Suite
```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1
collected 29 items

app/tests/test_adversarial_security.py::test_refresh_token_security_and_validation PASSED [  3%]
app/tests/test_adversarial_security.py::test_upload_path_traversal_sanitization PASSED [  6%]
app/tests/test_adversarial_security.py::test_cross_tenant_ai_action_execution_blocked PASSED [ 10%]
app/tests/test_adversarial_security.py::test_adversarial_prompt_injection_detection PASSED [ 13%]
app/tests/test_adversarial_security.py::test_deleted_document_excluded_from_rag PASSED [ 17%]
app/tests/test_ai_intents.py::test_all_eight_intents_recognized PASSED   [ 20%]
app/tests/test_ai_intents.py::test_action_suggestion_rules PASSED        [ 24%]
app/tests/test_analytics.py::test_analytics_overview_endpoint PASSED     [ 27%]
app/tests/test_auth.py::test_register_and_login_flow PASSED              [ 31%]
app/tests/test_auth.py::test_invalid_login PASSED                        [ 34%]
app/tests/test_conversations.py::test_conversation_lifecycle_and_messages PASSED [ 37%]
app/tests/test_customers.py::test_customer_crud_operations PASSED        [ 41%]
app/tests/test_documents.py::test_knowledge_document_lifecycle PASSED    [ 44%]
app/tests/test_documents.py::test_unsupported_file_upload_rejected PASSED [ 48%]
app/tests/test_extended_tenant_isolation.py::test_cross_tenant_conversation_isolation PASSED [ 51%]
app/tests/test_extended_tenant_isolation.py::test_cross_tenant_followup_isolation PASSED [ 55%]
app/tests/test_extended_tenant_isolation.py::test_cross_tenant_audit_logs_isolation PASSED [ 58%]
app/tests/test_followups.py::test_followup_crud_and_status PASSED        [ 62%]
app/tests/test_rag.py::test_scenario_1_fee_inquiry PASSED                [ 65%]
app/tests/test_rag.py::test_scenario_2_nonexistent_course_escalates PASSED [ 68%]
app/tests/test_rag.py::test_scenario_3_refund_request PASSED             [ 72%]
app/tests/test_rag.py::test_scenario_4_ai_followup_proposal_and_execution PASSED [ 75%]
app/tests/test_rag.py::test_scenario_5_prompt_injection_rejected PASSED  [ 79%]
app/tests/test_security.py::test_health_check_unauthenticated PASSED     [ 82%]
app/tests/test_security.py::test_unauthorized_endpoints_reject_invalid_token PASSED [ 86%]
app/tests/test_security.py::test_staff_role_cannot_access_owner_only_resources PASSED [ 89%]
app/tests/test_tenant_isolation.py::test_cross_tenant_customer_access_blocked PASSED [ 93%]
app/tests/test_tenant_isolation.py::test_tenant_spoofing_header_rejected PASSED [ 96%]
app/tests/test_tenant_isolation.py::test_rag_vector_search_tenant_isolation PASSED [100%]

============================= 29 passed in 18.98s =============================
```

### 2. AI Evaluation Benchmark
```
============================================================
  EVALUATION RESULTS SUMMARY
============================================================
  Total Test Cases:            9
  Intent Accuracy:             100.0% (9/9)
  Escalation Accuracy:         100.0% (9/9)
  Keyword / Grounding Match:   100.0% (9/9)
============================================================
```

### 3. Frontend Next.js Production Build
```
✓ Compiled successfully
✓ Generating static pages (13/13)
✓ Finalizing page optimization
All routes compiled with 0 TypeScript / runtime errors.
```

### 4. Demo Data Seeding
```
[Knowledge] Indexed courses.md (6 chunks)
[Knowledge] Indexed pricing.md (4 chunks)
[Knowledge] Indexed faq.md (4 chunks)
[Knowledge] Indexed refund-policy.md (3 chunks)
[Knowledge] Indexed timings.md (2 chunks)
[Customers] Created 8 demo customer profiles
[Conversations] Created 5 rich conversation threads with messages
[Followups] Created 4 initial operational follow-ups
```
