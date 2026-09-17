# OpsPilot Repository File Map

This document explains the purpose, responsibilities, and architecture of every important directory and file in the OpsPilot repository.

---

## Root Architecture

- `README.md`: Master project guide, setup instructions, architecture summary, and quickstart commands.
- `ARCHITECTURE.md`: High-level system architecture, Mermaid diagrams, security boundaries, and database relationships.
- `PROJECT_LOG.md`: Chronological log of real engineering decisions, tradeoffs, and outcomes.
- `docker-compose.yml`: Local & staging orchestration for PostgreSQL (pgvector), Redis, FastAPI backend, Celery worker, and Next.js frontend.
- `.env.example`: Template of all required application environment variables.
- `.gitignore`: Ignored paths for Python, Node, Next.js build artifacts, and secrets.
- `.github/workflows/ci.yml`: GitHub Actions CI pipeline executing linting, backend pytest suite, AI evaluation, and frontend Next.js production build.

---

## Backend (`backend/app/`)

### Core Layer (`backend/app/core/`)
- `config.py`: Centralized Pydantic `Settings` model managing environment variables, CORS, JWT secrets, database connection URLs, and RAG thresholds.
- `database.py`: SQLAlchemy asynchronous engine, session factory (`AsyncSessionLocal`), declarative Base model, and dependency provider (`get_db`).
- `security.py`: Password hashing using bcrypt (`get_password_hash`, `verify_password`) and JWT token encoding/decoding (`create_access_token`, `create_refresh_token`).
- `logging.py`: Structured logger configuration with request IDs and timestamps.

### Database Models (`backend/app/models/`)
- `base.py`: Abstract `BaseModel` defining UUID primary key (`id`) and UTC `created_at` / `updated_at` timestamps.
- `user.py`: `User` table for authentication credentials and profile information.
- `business.py`: `Business` tenant table for organizational settings.
- `membership.py`: `BusinessMember` relation table linking users to businesses with `OWNER` and `STAFF` roles.
- `customer.py`: `Customer` table with lifecycle statuses (`NEW`, `ACTIVE`, `FOLLOW_UP`, `RESOLVED`, `INACTIVE`).
- `conversation.py`: `Conversation` thread table with statuses (`OPEN`, `WAITING`, `HUMAN_REVIEW`, `RESOLVED`, `CLOSED`) and priority levels.
- `message.py`: `Message` timeline table tracking sender (`CUSTOMER`, `STAFF`, `AI`), intent, and confidence.
- `knowledge_document.py`: `KnowledgeDocument` record tracking uploaded files and ingestion status (`UPLOADED`, `PROCESSING`, `READY`, `FAILED`).
- `knowledge_chunk.py`: `KnowledgeChunk` vector table storing chunk text, 1536-dim embeddings, and metadata.
- `followup.py`: `Followup` task table tracking assignments, due dates, and completion status.
- `ai_interaction.py`: `AIInteraction` telemetry log capturing latency, token retrieval count, and confidence.
- `ai_action.py`: `AIAction` record managing proposed and executed automated workflows.
- `audit_log.py`: `AuditLog` table for tamper-evident business activity tracking without sensitive credentials.

### AI & RAG Engine (`backend/app/ai/`)
- `provider.py`: Abstract `LLMProvider` interface and concrete implementations (`MockLLMProvider`, `OpenAILLMProvider`, `GeminiLLMProvider`, `OllamaLLMProvider`).
- `service.py`: `AIService` orchestrating embedding generation, tenant-scoped vector search, intent classification, grounded answer synthesis, and human escalation.
- `prompts.py`: Strict system prompts for intent classification, grounded RAG QA, and operational action suggestions.
- `validator.py`: `AIValidator` containing regex patterns for prompt injection detection and business escalation rules.
- `chunking.py`: Semantic text cleaner and paragraph-aware chunker with token overlap.

### Application Services (`backend/app/services/`)
- `auth_service.py`: User registration, authentication, and JWT lifecycle.
- `business_service.py`: Business profile updates.
- `customer_service.py`: Customer CRUD, search, and pagination.
- `conversation_service.py`: Conversation status handling, staff replies, and customer simulation through the AI pipeline.
- `knowledge_service.py`: Document upload, file parsing (PDF/MD/TXT), chunking, vector indexing, and deletion.
- `followup_service.py`: Follow-up scheduling, overdue computation, and completion.
- `analytics_service.py`: Aggregation of operational KPIs, daily volume, intent distribution, and resolution ratios.
- `audit_service.py`: Redacted audit trail logging.

### API Endpoints (`backend/app/api/`)
- `deps.py`: Dependency injection for `get_current_user`, `get_current_business_membership` (tenant isolation gate), and `require_owner_role`.
- `v1/endpoints/auth.py`: `/api/v1/auth` (register, login, refresh, logout, me).
- `v1/endpoints/business.py`: `/api/v1/business` (view/update business profile).
- `v1/endpoints/customers.py`: `/api/v1/customers` (paginated search, CRUD).
- `v1/endpoints/conversations.py`: `/api/v1/conversations` (list, create, update status/priority).
- `v1/endpoints/messages.py`: `/api/v1/conversations/{id}/messages` and `/simulate-customer`.
- `v1/endpoints/knowledge.py`: `/api/v1/knowledge` (document upload, chunk inspection, search, delete).
- `v1/endpoints/followups.py`: `/api/v1/followups` (list, create, update status).
- `v1/endpoints/ai.py`: `/api/v1/ai` (classify, answer, suggest-action, execute-action).
- `v1/endpoints/analytics.py`: `/api/v1/analytics/overview`.
- `v1/endpoints/audit_logs.py`: `/api/v1/audit-logs`.

### Background Workers (`backend/app/workers/`)
- `celery_app.py`: Celery instance configuration with Redis broker.
- `tasks.py`: Asynchronous document processing and vectorization worker task.

### Test Suite (`backend/app/tests/`)
- `conftest.py`: Async SQLite test fixtures with Tenant A and Tenant B data.
- `test_auth.py`: Registration, login, token refresh, duplicate prevention.
- `test_tenant_isolation.py`: Cross-tenant data isolation and spoofing rejection tests.
- `test_customers.py`: Customer CRUD and search tests.
- `test_conversations.py`: Conversation lifecycle and message flow tests.
- `test_rag.py`: Scenarios 1-6 (fee inquiry, nonexistent course, refund request, follow-up suggestion, prompt injection, tenant isolation).
- `test_followups.py`: Task creation, overdue checking, and completion tests.
- `test_analytics.py`: Analytics KPI calculations.
- `test_security.py`: Role-based access control and unauthorized token rejection.

---

## Evaluation (`evaluation/`)

- `dataset.json`: Golden test dataset across 7 categories (ANSWERABLE, UNANSWERABLE, AMBIGUOUS, SENSITIVE, PROMPT_INJECTION, CONFLICTING_INFORMATION, HALLUCINATION_TRAP).
- `run_eval.py`: Automated evaluation runner calculating intent accuracy, grounded answer rate, and escalation fidelity.

---

## Scripts (`scripts/`)

- `seed_data.py`: Database population script creating "Demo Learning Center" demo data (8 customers, 5 conversation threads, 4 follow-up tasks, 5 vectorized knowledge documents).
- `demo_knowledge/`: Source markdown knowledge files (`courses.md`, `pricing.md`, `faq.md`, `refund-policy.md`, `timings.md`).

---

## Frontend (`frontend/src/`)

- `lib/api.ts`: Typed API client for all backend endpoints with JWT token injection.
- `lib/utils.ts`: Tailwind class merger and date formatting helpers.
- `context/AuthContext.tsx`: React Context managing user session, active business tenant, and login/logout state.
- `components/Sidebar.tsx`: Navigation bar with active business tenant badge.
- `components/Header.tsx`: Top bar with user profile badge and RAG status indicator.
- `components/AppLayout.tsx`: Authenticated app layout shell with route protection.
- `components/StatusBadges.tsx`: Color-coded status and priority chips.
- `app/layout.tsx`: Root HTML shell with dark theme and AuthProvider.
- `app/login/page.tsx`: Sign-in screen with 1-click demo login buttons.
- `app/register/page.tsx`: Business registration and workspace provisioning screen.
- `app/dashboard/page.tsx`: Executive dashboard with KPI cards, volume chart, intent breakdown, and recent activity.
- `app/conversations/page.tsx`: 3-column desktop inbox with message timeline, customer simulation, and AI Decision Inspector.
- `app/customers/page.tsx` & `[id]/page.tsx`: Customer directory with paginated search and detail editor.
- `app/knowledge/page.tsx`: Knowledge base dropzone, document status table, chunk inspector modal, and RAG retrieval sandbox.
- `app/followups/page.tsx`: Follow-up task manager with Pending, Overdue, and Completed tabs.
- `app/analytics/page.tsx`: Performance dashboard with resolution rates, response times, and daily charts.
- `app/settings/page.tsx`: Business profile manager, AI safety sliders, and audit logs viewer.
