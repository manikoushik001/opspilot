# OpsPilot Comprehensive Project Guide

Welcome to the OpsPilot developer guide. This document explains the architecture, design choices, codebase structure, operational patterns, and mental model of the OpsPilot platform.

---

## 1. What OpsPilot Is
OpsPilot is a multi-tenant, AI-powered customer operations platform built for small service-oriented businesses (demonstrated via the fictional "Demo Learning Center"). It transforms fragmented customer communications into a centralized, grounded, observable system.

---

## 2. Core Architectural Philosophy
> **"AI proposes. Application validates. Business rules decide. System executes."**

- The LLM does **NOT** have direct database access, tool execution permissions, or unrestricted shell privileges.
- Every AI output is treated as untrusted until validated through Pydantic schemas, authenticated context, tenant authorization boundaries, and domain rules.

---

## 3. Technology Stack Breakdown

### Backend
- **FastAPI**: Asynchronous Python API framework offering automatic OpenAPI documentation, high concurrency, and strict runtime type validation via Pydantic v2.
- **SQLAlchemy 2.0 (Async)**: Type-safe declarative ORM with explicit transaction boundaries and support for PostgreSQL asyncpg and SQLite aiosqlite.
- **PostgreSQL + pgvector**: Unified relational database and high-dimensional vector search engine.
- **Redis & Celery**: Task queue for asynchronous document processing and embedding generation.
- **Pytest**: Comprehensive test suite with async fixtures and tenant isolation tests.

### Frontend
- **Next.js 14 (App Router)**: Modern React framework with server-side generation, dynamic route handling, and high-performance client transitions.
- **TypeScript**: Complete static type safety matching backend Pydantic models.
- **Tailwind CSS**: Utility-first CSS tailored for modern dark/light SaaS aesthetics.
- **Lucide Icons**: Crisp, accessible icon set.

---

## 4. Key Subsystems & Domain Modules

### 4.1 Authentication & Multi-Tenancy
- **Users & Memberships**: Users authenticate via email and password (hashed with bcrypt). Upon registration, a tenant `Business` is provisioned and the user is linked via `BusinessMember` with role `OWNER`.
- **Tenant Isolation Middleware**: The `get_current_business_membership` dependency in `app/api/deps.py` guarantees that requests are strictly verified against the user's business memberships. Cross-tenant spoofing attempts immediately return `HTTP 403 Forbidden`.

### 4.2 Conversations & Chronological Inbox
- Conversations are multi-channel interaction threads belonging to a customer and tenant.
- Statuses: `OPEN`, `WAITING`, `HUMAN_REVIEW`, `RESOLVED`, `CLOSED`.
- Messages record sender type (`CUSTOMER`, `STAFF`, `AI`), intent, and confidence score.

### 4.3 Knowledge Ingestion & Document Processing
- Supports PDF, Markdown (.md), and plain text.
- Documents are cleaned, chunked into 500-character segments with 50-character overlap, and converted into 1536-dimensional vector embeddings stored in `knowledge_chunks`.

### 4.4 Grounded RAG & Human-in-the-Loop Escalation
1. **Intent Classification**: Customer queries are categorized into 8 distinct intents (`COURSE_INFORMATION`, `PRICE_QUERY`, `APPOINTMENT_REQUEST`, `COMPLAINT`, `REFUND_REQUEST`, `FOLLOW_UP`, `GENERAL_INFORMATION`, `OTHER`).
2. **Tenant Vector Search**: Cosine similarity search scoped strictly to the active `business_id`.
3. **Grounding Guard**: The LLM synthesizes answers referencing only retrieved chunk indexes. If no relevant source is found or confidence is low, the conversation automatically escalates to `HUMAN_REVIEW`.

### 4.5 Follow-ups & AI Action Proposal
- When a customer says "I'll decide tomorrow", the AI proposes a `CREATE_FOLLOWUP` action.
- The user can validate and execute the action via the Controlled Action Execution endpoint (`/api/v1/ai/execute-action`).
- Follow-ups support status tracking (`PENDING`, `COMPLETED`, `CANCELLED`) and automatic overdue detection.

### 4.6 Analytics & Telemetry
- Aggregates total customers, active conversations, AI resolution rate, mean confidence, daily volume, and intent distributions.
- AI telemetry records model, operation, confidence, latency, and retrieval count in `ai_interactions`.

### 4.7 Redacted Audit Logs
- Every state change is recorded in `audit_logs` with actor ID, action type, and resource details. All sensitive tokens, passwords, and authorization headers are scrubbed and marked `[REDACTED]`.

---

## 5. Local Setup & Quickstart

```bash
# 1. Clone repository
cd opspilot

# 2. Backend Setup
cd backend
pip install -r requirements.txt
python -m pytest -v app/tests

# 3. Seed Demo Data
cd ..
python scripts/seed_data.py

# 4. Frontend Setup & Build
cd frontend
npm install
npm run build

# 5. Run with Docker Compose
docker-compose up --build
```
