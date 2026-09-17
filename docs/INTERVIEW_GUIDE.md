# OpsPilot Technical Interview Guide

This guide compiles high-signal architectural, backend, frontend, database, AI/RAG, security, and scaling interview questions based strictly on the real OpsPilot codebase.

---

## Architecture & System Design

### Q1: Why did you choose a Modular Monolith instead of Microservices?
- **Short Answer**: To ensure strict relational transactional integrity between conversations, customers, follow-ups, and audit trails without distributed network latency or operational complexity.
- **Detailed Answer**: OpsPilot requires ACID guarantees within tenant boundaries (e.g. creating a customer message, updating conversation status, logging an AI action, and generating an audit trail in a single cohesive flow). A modular monolith with clean domain boundaries (`app/api`, `app/services`, `app/models`, `app/ai`, `app/workers`) delivers exceptional separation of concerns, rapid development iteration, and simple single-container deployment without premature microservice overhead.
- **Relevant File**: [backend/app/main.py](file:///c:/Users/manik/opspilot/backend/app/main.py), [ARCHITECTURE.md](file:///c:/Users/manik/opspilot/ARCHITECTURE.md).

### Q2: How does OpsPilot enforce Tenant Isolation and prevent cross-tenant data leakage?
- **Short Answer**: Through FastAPI dependency injection (`get_current_business_membership`) that verifies user membership and enforces row-level `WHERE business_id = :tenant_id` scoping on every SQL and vector query.
- **Detailed Answer**: Tenant boundaries are never entrusted to frontend filtering. Every protected endpoint extracts the authenticated user from the JWT and looks up their active `business_id` from their `BusinessMember` record or `X-Business-ID` header. If a user attempts to access a resource from another business, the application immediately throws `HTTP 403 Forbidden` or `HTTP 404 Not Found`. Automated cross-tenant unit tests in `test_tenant_isolation.py` explicitly verify this.
- **Relevant File**: [backend/app/api/deps.py](file:///c:/Users/manik/opspilot/backend/app/api/deps.py), [backend/app/tests/test_tenant_isolation.py](file:///c:/Users/manik/opspilot/backend/app/tests/test_tenant_isolation.py).

---

## AI & RAG Engineering

### Q3: How do you prevent LLM hallucinations in customer support conversations?
- **Short Answer**: Through a multi-stage guarded RAG pipeline, strict system prompts, similarity thresholding, and automated human escalation.
- **Detailed Answer**: When a customer sends a message, OpsPilot embeds the query and executes a tenant-scoped cosine similarity search against `knowledge_chunks`. If no chunk exceeds the similarity threshold (`RAG_SIMILARITY_THRESHOLD`), or if the question pertains to sensitive topics (refunds, legal complaints) or prompt injection, the system refuses to generate speculative answers and immediately transitions the conversation status to `HUMAN_REVIEW`.
- **Relevant File**: [backend/app/ai/service.py](file:///c:/Users/manik/opspilot/backend/app/ai/service.py), [backend/app/ai/validator.py](file:///c:/Users/manik/opspilot/backend/app/ai/validator.py).

### Q4: Why can't the LLM directly execute database mutations or tool actions?
- **Short Answer**: "AI proposes, Application validates, Business rules decide, System executes."
- **Detailed Answer**: Giving an LLM direct SQL execution or tool privileges creates severe prompt injection and data corruption vulnerabilities. In OpsPilot, the AI can only return structured action proposals (e.g. `CREATE_FOLLOWUP`, `UPDATE_CUSTOMER_STATUS`). The proposal must pass through Pydantic schema validation, user authentication, customer ownership checks, and business logic before being executed.
- **Relevant File**: [backend/app/api/v1/endpoints/ai.py](file:///c:/Users/manik/opspilot/backend/app/api/v1/endpoints/ai.py), [backend/app/models/ai_action.py](file:///c:/Users/manik/opspilot/backend/app/models/ai_action.py).

---

## Database & Vector Storage

### Q5: Why PostgreSQL with pgvector instead of a standalone vector database like Pinecone?
- **Short Answer**: Single database engine for both relational transactional data and vector embeddings, eliminating synchronization lag and reducing infrastructure cost.
- **Detailed Answer**: Using PostgreSQL 16 with `pgvector` allows OpsPilot to perform single-query tenant-filtered vector searches (`SELECT * FROM knowledge_chunks WHERE business_id = :id ORDER BY embedding <=> :query_vec LIMIT 4`). It eliminates network hops to external vector databases, avoids dual-write consistency bugs, and leverages standard PostgreSQL backup, replication, and indexing tools.
- **Relevant File**: [backend/app/models/knowledge_chunk.py](file:///c:/Users/manik/opspilot/backend/app/models/knowledge_chunk.py), [docker-compose.yml](file:///c:/Users/manik/opspilot/docker-compose.yml).

---

## Security & Reliability

### Q6: How does OpsPilot defend against Prompt Injection attacks?
- **Short Answer**: Multi-layered defense combining pre-execution regex signature scanning, strict system prompt isolation, and controlled action validation.
- **Detailed Answer**: Incoming messages are scanned by `AIValidator.detect_prompt_injection` for known jailbreak patterns (`ignore previous instructions`, `developer mode`, `show system prompt`, `execute sql`). If detected, the AI execution is aborted, the event is recorded in `audit_logs`, and the conversation is escalated to human staff.
- **Relevant File**: [backend/app/ai/validator.py](file:///c:/Users/manik/opspilot/backend/app/ai/validator.py), [backend/app/tests/test_rag.py](file:///c:/Users/manik/opspilot/backend/app/tests/test_rag.py).

### Q7: What would you change in the architecture at 100x scale?
- **Short Answer**: Database read replicas with tenant sharding, asynchronous message ingestion via Redis Streams, dedicated vector index caching, and distributed Celery worker clusters.
- **Detailed Answer**:
  1. **Database**: Implement read replicas for analytics queries and consider tenant-based horizontal sharding or Citus for multi-million tenant scales.
  2. **RAG Caching**: Add a Redis semantic cache layer for high-frequency repeated inquiries (e.g. course fees, operating hours) to bypass LLM inference latency.
  3. **Background Ingestion**: Scale Celery document processing workers independently using Kubernetes HPA or dedicated container instances.
