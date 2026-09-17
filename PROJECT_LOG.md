# OpsPilot Engineering Project Log

This log tracks all architectural and engineering decisions made during the design, development, testing, and deployment preparation of OpsPilot.

---

### Decision Log Entry 001: Modular Monolith vs Microservices
- **Phase**: Architecture Design
- **Context**: Initial system architecture and repository setup for multi-tenant SaaS application OpsPilot.
- **Problem**: Need a robust, maintainable, secure architecture that enforces strict multi-tenancy, deterministic AI response generation, vector search (RAG), background processing, and modern frontend capabilities.
- **Options**:
  1. Microservices architecture with separate services for Auth, RAG, Ingestion, and Messaging.
  2. Modular Monolith using FastAPI (Python) for backend with clean service boundaries + Next.js (TypeScript) frontend.
- **Decision**: Modular Monolith with FastAPI and Next.js.
- **Reason**: OpsPilot has high relational consistency requirements (conversations, customers, membership, audit logs) alongside vector similarity search. A modular monolith simplifies deployment, guarantees transactional integrity within tenant boundaries, eliminates distributed network latency, and avoids premature microservice overhead while keeping domain modules strictly separated.
- **Tradeoffs**: Backend scaling is unified rather than per-service, which is ideal for MVP through growth stages.
- **Result**: Implemented modular backend directory structure with dedicated service, repository, and AI layers.

---

### Decision Log Entry 002: Multi-Tenant Isolation Strategy
- **Phase**: Data Modeling & Security
- **Context**: Multi-tenant isolation strategy.
- **Problem**: Preventing Business A from accessing or mutating Business B's data at the database and API levels.
- **Options**:
  1. Separate database per tenant (high operational complexity and cost).
  2. Shared schema with row-level tenant filtering (`business_id` enforced in application layer and queries).
  3. Separate PostgreSQL schemas per tenant.
- **Decision**: Shared schema with explicit row-level `business_id` scoping in every database query, enforced through FastAPI dependency injection (`get_current_business_membership`).
- **Reason**: Simplifies migrations, pooling, and vector indexing while providing rigorous programmatic tenant boundary enforcement.
- **Tradeoffs**: Requires strict code discipline and automated cross-tenant security unit tests.
- **Result**: Every model includes `business_id`, foreign keys, and indexes. All repository/service methods require explicit tenant scope.

---

### Decision Log Entry 003: AI & RAG Safety Framework
- **Phase**: AI Engineering
- **Context**: AI and RAG Safety Framework ("AI proposes, Application validates, Business rules decide, System executes").
- **Problem**: Preventing LLM hallucinations, SQL injection, arbitrary code execution, and prompt leakage.
- **Options**:
  1. Direct tool calling where the LLM executes database queries or API endpoints.
  2. Multi-stage guarded pipeline: Intent Classification -> Scoped Vector Search -> Grounded LLM generation -> Schema validation -> Business rule verification -> Application execution.
- **Decision**: Multi-stage guarded pipeline with structured Pydantic schema validation.
- **Reason**: Guarantees that the LLM cannot mutate data or read unauthorized records directly. Any action suggested by the LLM (e.g., `CREATE_FOLLOWUP`, `ESCALATE_TO_HUMAN`) is purely a proposal that the application validates against tenant permissions before committing.
- **Tradeoffs**: Adds a validation layer and slight latency, but provides enterprise-grade safety and explainability.
- **Result**: `AIService` and `AIValidator` components created with support for pluggable LLM providers (Mock, OpenAI, Gemini, Ollama).

---

### Decision Log Entry 004: Vector Database and Embedding Storage
- **Phase**: RAG & Search Architecture
- **Context**: Vector Database and Embedding Storage.
- **Problem**: Storing and searching high-dimensional embeddings for knowledge base documents.
- **Options**:
  1. External vector DB (Pinecone, Qdrant, Weaviate).
  2. PostgreSQL with `pgvector` extension.
- **Decision**: PostgreSQL with `pgvector` extension (with fallback normalized cosine search in memory/SQL for environments without pgvector).
- **Reason**: Unifies relational transactional data and vector data in a single ACID-compliant database. Enables single-query joins and tenant-filtered vector retrieval (`WHERE business_id = :id ORDER BY embedding <=> :query_vec LIMIT :k`).
- **Tradeoffs**: Index maintenance handled inside PostgreSQL; well-suited for document scales up to millions of chunks.
- **Result**: Created `knowledge_documents` and `knowledge_chunks` tables with pgvector support.
