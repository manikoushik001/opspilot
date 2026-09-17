# OpsPilot Product Decisions & Design Rationale

## 1. Modular Monolith vs. Microservices
- **Decision**: Implemented a Modular Monolith backend using FastAPI and SQLAlchemy 2.0.
- **Rationale**: OpsPilot is a high-consistency relational SaaS where customers, conversations, messages, follow-ups, and audit trails share strict ACID transactions. Introducing microservices prematurely adds network serialization latency, distributed transaction complexity, and multi-service deployment overhead. The modular monolith provides clean domain separation (`app/api`, `app/services`, `app/models`, `app/ai`, `app/workers`) while maintaining unified transactional integrity.

## 2. Multi-Tenancy Isolation Pattern
- **Decision**: Shared schema with row-level tenant filtering scoped by `business_id` and enforced via FastAPI dependency injection.
- **Rationale**: Provides optimal resource utilization and simple schema migrations with Alembic, while guaranteeing complete tenant isolation at the query level. Every API route and database repository method explicitly filters by `business_id`.

## 3. "AI Proposes, System Executes" Architecture
- **Decision**: The LLM is never given direct write access, SQL query privileges, or tool execution rights.
- **Rationale**: An autonomous SaaS platform must never let an untrusted model mutate critical business records. Instead, the AI generates structured proposals (e.g. `CREATE_FOLLOWUP`, `ESCALATE_TO_HUMAN`) that pass through Pydantic schema validation, user authentication, tenant authorization, and business rules before being committed.

## 4. PostgreSQL with pgvector for Relational & Vector Storage
- **Decision**: PostgreSQL 16 with `pgvector` extension.
- **Rationale**: Unifies operational relational tables (`customers`, `conversations`, `followups`) and 1536-dimensional vector embeddings in a single database engine. Eliminates synchronization lag between separate vector databases and relational databases, and allows single-query tenant-isolated similarity searches (`WHERE business_id = :id ORDER BY embedding <=> :query_vector LIMIT 4`).

## 5. Next.js 14 App Router with Tailwind CSS & TanStack Query
- **Decision**: Modern Next.js TypeScript frontend with rich dark theme, 3-column inbox layout, and real-time state management.
- **Rationale**: Delivers instant reactivity, fast client-side navigation, accessible form handling, and responsive desktop-to-mobile layouts.
