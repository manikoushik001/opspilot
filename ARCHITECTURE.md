# OpsPilot System Architecture

OpsPilot is a multi-tenant, AI-powered customer operations SaaS platform designed for small businesses to manage customer conversations, centralize operational knowledge, execute grounded RAG answers, automate follow-up workflows, and maintain strict tenant isolation.

---

## 1. High-Level Component Architecture

```mermaid
graph TD
    Client[Next.js Modern Frontend<br/>TypeScript / Tailwind / TanStack Query]
    API[FastAPI Modular Monolith<br/>Auth / Business / Customers / Conversations / RAG / Followups]
    Postgres[(PostgreSQL + pgvector<br/>Tenant-Isolated Schema & Vectors)]
    Redis[(Redis Cache & Queue<br/>Rate Limiting / Celery Broker)]
    Worker[Celery Background Worker<br/>Document Extraction & Vectorization]
    AISvc[AI & RAG Engine<br/>Intent / RAG / Grounding / Action System]
    LLM[Pluggable LLM Provider<br/>Mock / OpenAI / Gemini / Ollama]

    Client -->|REST API + JWT| API
    API -->|Async SQLAlchemy| Postgres
    API -->|Enqueue Processing Jobs| Redis
    Redis -->|Dequeue Jobs| Worker
    Worker -->|Read/Store Chunks & Embeddings| Postgres
    Worker -->|Create Embeddings| AISvc
    API -->|Execute Inferences & Actions| AISvc
    AISvc -->|Embeddings & Completions| LLM
```

---

## 2. Multi-Tenant Security & Isolation Model

Tenant isolation is strictly enforced at the application and query layers:

```mermaid
flowchart LR
    Request[HTTP Request] --> JWT[JWT Verification & User Extraction]
    JWT --> Member[Business Membership Check]
    Member --> Scope[Inject tenant `business_id`]
    Scope --> Query["SQL Query with WHERE business_id = :tenant_id"]
    Query --> DB[(Database / pgvector)]
```

### Core Security Rules:
1. **Zero Cross-Tenant Leakage**: Every database read, write, update, vector similarity search, and audit log contains an explicit `business_id` predicate.
2. **Role-Based Access Control (RBAC)**:
   - `OWNER`: Full control over business settings, staff members, knowledge base, analytics, customer data, and conversations.
   - `STAFF`: Operational access to conversations, messaging, follow-ups, and customer records.
3. **No Direct Tool/Database Execution by LLM**:
   - The LLM only receives sanitized context and returns structured JSON responses.
   - Proposed actions (e.g., `CREATE_FOLLOWUP`, `ESCALATE_TO_HUMAN`) pass through schema validation, ownership checks, and business rules before execution.

---

## 3. RAG Pipeline & AI Safety Flow

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Simulated User
    participant API as Conversations API
    participant AI as AIService
    participant PG as PostgreSQL (pgvector)
    participant LLM as LLM Provider
    participant Escalation as Human Escalation Manager

    Customer->>API: Post Message ("What is the Java course fee?")
    API->>AI: Classify Intent & Scan Injections
    AI->>LLM: Intent Classification Prompt
    LLM-->>AI: Intent: PRICE_QUERY (Confidence: 0.95)
    
    API->>AI: Execute RAG Retrieval
    AI->>LLM: Generate Query Embedding
    LLM-->>AI: Vector [0.012, -0.043, ...]
    AI->>PG: Cosine Similarity Search (WHERE business_id = X)
    PG-->>AI: Top-K Grounded Chunks (pricing.md)
    
    AI->>LLM: Grounded QA Prompt (Context + Question)
    LLM-->>AI: Structured Draft Answer
    
    AI->>AI: Grounding Validation & Safety Checks
    alt Confidence >= Threshold & Grounded
        AI-->>API: Verified Grounded Answer
        API->>Customer: Safe Response with Decision Metadata
    else Low Confidence / No Sources / Prompt Injection / Refund Request
        AI->>Escalation: Trigger Human Escalation
        Escalation->>API: Update Conversation Status = HUMAN_REVIEW
        API->>Customer: "I have escalated your query to our support team."
    end
```

---

## 4. Database Schema Relationships

```mermaid
erDiagram
    USERS ||--o{ BUSINESS_MEMBERS : has
    BUSINESSES ||--o{ BUSINESS_MEMBERS : includes
    BUSINESSES ||--o{ CUSTOMERS : owns
    BUSINESSES ||--o{ CONVERSATIONS : owns
    BUSINESSES ||--o{ KNOWLEDGE_DOCUMENTS : owns
    BUSINESSES ||--o{ FOLLOWUPS : tracks
    BUSINESSES ||--o{ AUDIT_LOGS : records
    
    CUSTOMERS ||--o{ CONVERSATIONS : participates
    CUSTOMERS ||--o{ FOLLOWUPS : assigned
    
    CONVERSATIONS ||--o{ MESSAGES : contains
    CONVERSATIONS ||--o{ AI_INTERACTIONS : logs
    CONVERSATIONS ||--o{ AI_ACTIONS : proposes
    
    KNOWLEDGE_DOCUMENTS ||--o{ KNOWLEDGE_CHUNKS : contains
```

---

## 5. Technology Stack Summary

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Next.js (App Router), TypeScript, Tailwind CSS, TanStack Query, Lucide Icons, Radix UI | Fast, responsive, accessible, enterprise-grade UX with dynamic state management. |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 | High-performance asynchronous API, auto-generated OpenAPI docs, strict runtime type validation. |
| **ORM / DB Access** | SQLAlchemy 2.0 (Async + Sync) + Alembic | Declarative modeling, type-safe queries, reliable schema migrations. |
| **Database** | PostgreSQL 16 + pgvector | ACID relational integrity + native high-dimensional vector similarity search in a single engine. |
| **Task Queue & Cache** | Redis 7 + Celery | Scalable asynchronous document chunking, embedding generation, and rate limiting. |
| **AI / RAG** | Provider-agnostic abstraction (Mock, OpenAI, Gemini, Ollama) | Zero vendor lock-in, fully testable offline with deterministic mock provider or live LLMs. |
| **Containerization** | Docker, Docker Compose | Reproducible local and staging deployment with 1-command startup. |
