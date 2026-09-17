# OpsPilot Security Architecture & Hardening

OpsPilot implements defense-in-depth across authentication, authorization, multi-tenant boundaries, prompt injection defense, and audit logging.

---

## 1. Authentication & Token Security
- **Password Hashing**: Passwords are cryptographically salted and hashed using `bcrypt` (12 rounds).
- **JWT Lifecycle**:
  - Access Tokens: Short-lived (60 minutes), signed with `HS256`, containing only user ID (`sub`), expiration timestamp (`exp`), and token type (`type: "access"`).
  - Refresh Tokens: Long-lived (7 days), stored securely and required for rotating access tokens.
- **Account Inactivation**: Inactive user accounts are rejected at both token decode and endpoint verification layers.

---

## 2. Multi-Tenant Authorization & Tenant Isolation
- **Tenant Scope Enforcement**:
  - The `get_current_business_membership` dependency verifies that the user is an active member of the business specified by the `X-Business-ID` header.
  - If a user from Business A attempts to pass `X-Business-ID: biz-b-222`, the system rejects the request immediately with `HTTP 403 Forbidden`.
  - Every SQL query across `customers`, `conversations`, `messages`, `knowledge_documents`, `knowledge_chunks`, `followups`, and `ai_actions` includes an explicit `WHERE business_id = :tenant_id` clause.
- **Role-Based Access Control (RBAC)**:
  - `OWNER`: Can modify business settings, delete documents, manage team members, and view audit logs.
  - `STAFF`: Can view customers, participate in conversations, send messages, execute follow-ups, and trigger AI operations.

---

## 3. Prompt Injection & Malicious Input Defense
Customer messages are treated as untrusted input:
- Pre-execution regex filtering for jailbreak patterns (`"ignore previous instructions"`, `"developer mode"`, `"show system prompt"`, `"execute sql"`, `"drop table"`).
- Strict system prompts forbidding the model from revealing private instructions or accepting prompt override requests.
- No direct database access or tool execution privileges for the LLM.

---

## 4. Redacted Audit Trail Logging
All critical operations (`USER_REGISTERED`, `LOGIN`, `CUSTOMER_CREATED`, `CUSTOMER_UPDATED`, `CUSTOMER_DELETED`, `CONVERSATION_CREATED`, `MESSAGE_SENT`, `KNOWLEDGE_UPLOADED`, `AI_ESCALATED`, `AI_ACTION_EXECUTED`, `FOLLOWUP_CREATED`, `FOLLOWUP_COMPLETED`) are logged to the `audit_logs` table.
- Sanitization: Passwords, tokens, API keys, and authorization headers are stripped and marked `[REDACTED]` prior to persistence.
