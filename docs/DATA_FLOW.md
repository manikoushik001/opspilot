# OpsPilot Complete Data Flow Specification

This document details the step-by-step lifecycle of data transformations, authorizations, and executions across OpsPilot.

---

## 1. User Registration & Tenant Provisioning
```
POST /api/v1/auth/register
   │
   ├─► 1. Validate Email, Name, and Password via Pydantic (`UserCreate`)
   ├─► 2. Hash Password using bcrypt (`get_password_hash`)
   ├─► 3. Insert `users` record
   ├─► 4. Insert `businesses` record (defaulting to user's business name)
   ├─► 5. Insert `business_members` record with role `OWNER`
   ├─► 6. Write `audit_logs` record ("USER_REGISTERED")
   └─► 7. Return sanitized `UserOut` with membership list (passwords redacted)
```

---

## 2. Authentication & JWT Token Issuance
```
POST /api/v1/auth/login
   │
   ├─► 1. Query `users` by email
   ├─► 2. Verify password hash using `bcrypt.checkpw`
   ├─► 3. Check `is_active == True`
   ├─► 4. Issue HS256 JWT Access Token (60 min expiry) & Refresh Token (7 day expiry)
   ├─► 5. Write `audit_logs` record ("LOGIN")
   └─► 6. Return `{ access_token, refresh_token, token_type: "bearer" }`
```

---

## 3. Multi-Tenant Request Authorization Gate
Every protected resource request goes through FastAPI dependency injection:
```
Client HTTP Request (Headers: Authorization: Bearer <token>, X-Business-ID: <biz_id>)
   │
   ├─► `get_current_user`: Decodes JWT subject, queries `users` table
   ├─► `get_current_business_membership`:
   │      - Queries `business_members` WHERE user_id = :uid AND business_id = :biz_id
   │      - Rejects with HTTP 403 Forbidden if user does not belong to the tenant
   └─► Injects `(user, membership)` into route handler
```

---

## 4. Customer Creation & Scoped CRUD
```
POST /api/v1/customers
   │
   ├─► 1. Enforce tenant scope: `business_id = membership.business_id`
   ├─► 2. Validate input schema (`CustomerCreate`)
   ├─► 3. Insert `customers` record
   ├─► 4. Write `audit_logs` ("CUSTOMER_CREATED")
   └─► 5. Return `CustomerOut`
```

---

## 5. Customer Message & AI RAG Ingestion Flow
```
POST /api/v1/conversations/{id}/simulate-customer
   │
   ├─► 1. Verify conversation belongs to tenant `business_id`
   ├─► 2. Classify Intent & Scan Injections:
   │      - Regex scan for prompt injection signatures
   │      - Classify intent into 1 of 8 categories with confidence score
   ├─► 3. Insert customer `messages` record with `intent` and `ai_confidence`
   ├─► 4. Vector Retrieval (Tenant-Scoped):
   │      - Create query embedding vector
   │      - Cosine similarity search against `knowledge_chunks` WHERE `business_id = :tenant_id`
   │      - Filter chunks with similarity >= RAG_SIMILARITY_THRESHOLD
   ├─► 5. Grounded LLM Response Generation:
   │      - Pass retrieved chunks + customer message into strict grounding prompt
   │      - Synthesize structured draft answer
   ├─► 6. Grounding Validation & Human Escalation:
   │      - If low confidence, no sources, refund query, complaint, or prompt injection:
   │        Set `is_escalated = True`, conversation status = `HUMAN_REVIEW`, priority = `HIGH`
   ├─► 7. AI Action Proposal:
   │      - If customer requested delayed decision ("decide tomorrow"), propose `CREATE_FOLLOWUP`
   │      - Store proposed action in `ai_actions` table
   ├─► 8. Insert AI response `messages` record
   ├─► 9. Record `ai_interactions` telemetry
   └─► 10. Return customer message, AI message, and safe decision metadata
```

---

## 6. Controlled AI Action Execution Gate
```
POST /api/v1/ai/execute-action
   │
   ├─► 1. Validate payload schema (`AIActionExecuteRequest`)
   ├─► 2. Verify `conversation_id` and `customer_id` belong to active tenant
   ├─► 3. Check requested `action_type`:
   │      - `CREATE_FOLLOWUP`: Verify due date, insert `followups` record
   │      - `ESCALATE_TO_HUMAN`: Update conversation status to `HUMAN_REVIEW`
   │      - `UPDATE_CUSTOMER_STATUS`: Validate enum and update `customer.status`
   ├─► 4. Update `ai_actions.status = "EXECUTED"`
   ├─► 5. Write `audit_logs` ("AI_ACTION_EXECUTED")
   └─► 6. Return `{ success: true, result: "<action summary>" }`
```

---

## 7. Knowledge Document Upload & Ingestion Pipeline
```
POST /api/v1/knowledge/documents (Multipart File)
   │
   ├─► 1. Enforce OWNER role (`require_owner_role`)
   ├─► 2. Validate file extension (.pdf, .md, .txt)
   ├─► 3. Save raw file to storage backend (`uploads/`)
   ├─► 4. Insert `knowledge_documents` (status = "PROCESSING")
   ├─► 5. Text Extraction (Page-preserving text parsing for PDF/MD)
   ├─► 6. Semantic Chunking (500 chars with 50-char overlap)
   ├─► 7. Vector Embedding Generation (1536-dim embeddings)
   ├─► 8. Batch Insert `knowledge_chunks` with `business_id` and metadata
   ├─► 9. Update `knowledge_documents.status = "READY"`, `chunk_count = N`
   └─► 10. Write `audit_logs` ("KNOWLEDGE_UPLOADED")
```
