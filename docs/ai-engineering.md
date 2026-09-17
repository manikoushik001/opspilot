# OpsPilot AI Engineering & RAG Architecture

## 1. Multi-Stage AI Pipeline

OpsPilot implements a strict, multi-stage guarded pipeline for customer messages:

```
Customer Message
      │
      ▼
1. Prompt Injection Scanner & Safety Defense (`AIValidator`)
      │
      ▼
2. Intent Classification (`AIService.classify_intent`)
   ├─► 8 Standard Intents:
   │   (COURSE_INFORMATION, PRICE_QUERY, APPOINTMENT_REQUEST, COMPLAINT,
   │    REFUND_REQUEST, FOLLOW_UP, GENERAL_INFORMATION, OTHER)
   └─► Confidence Scoring & Telemetry Logging
      │
      ▼
3. Tenant-Isolated Vector Retrieval (`AIService.retrieve_context`)
   ├─► Generate Query Embedding Vector (1536-dim)
   ├─► Query `knowledge_chunks` WHERE `business_id = :tenant_id`
   └─► Filter Top-K Chunks with Cosine Similarity >= `RAG_SIMILARITY_THRESHOLD` (0.50)
      │
      ▼
4. Grounded Answer Synthesis (`LLMProvider.generate_rag_answer`)
   ├─► Formulate system prompt with strict grounding constraints
   └─► Generate structured response referencing verified chunk indexes
      │
      ▼
5. Validation & Human-in-the-Loop Escalation (`AIValidator`)
   ├─► Check Confidence: If < 0.75, escalate to `HUMAN_REVIEW`
   ├─► Check Sources: If zero verified chunks match, escalate
   ├─► Check Intent: If `REFUND_REQUEST` or `COMPLAINT`, escalate
   └─► Check Keywords: If customer asks for human manager or legal, escalate
      │
      ▼
6. Controlled Operational Action Proposal (`AIService.suggest_action`)
   ├─► Propose `CREATE_FOLLOWUP` for delayed decisions ("decide tomorrow")
   ├─► Propose `UPDATE_CUSTOMER_STATUS` for confirmed enrollment
   └─► Persist proposal in `ai_actions` table for validation & execution
```

## 2. Pluggable LLM Provider Abstraction
The `LLMProvider` interface decouples OpsPilot from specific LLM vendors:
- `MockLLMProvider`: Deterministic offline semantic vector embeddings and rule-based inference for offline demos, CI/CD, and pytest evaluation suites.
- `OpenAILLMProvider`: Live OpenAI API integration (GPT-4o-mini / text-embedding-3-small).
- `GeminiLLMProvider`: Google Gemini 1.5 Pro / Flash integration.
- `OllamaLLMProvider`: Local private LLM execution via Ollama (Llama 3 / Mistral).

## 3. Evaluation Dataset & Metrics
OpsPilot includes an automated evaluation suite (`evaluation/run_eval.py`) that benchmarks RAG and Intent accuracy across 7 test categories:
- `ANSWERABLE`: Routine inquiries with clear grounding in knowledge documents.
- `UNANSWERABLE`: Inquiries regarding non-existent courses or services (tests hallucination refusal).
- `AMBIGUOUS`: Vague statements testing low-confidence escalation.
- `SENSITIVE`: Refund requests and customer dissatisfaction.
- `PROMPT_INJECTION`: Jailbreak attempts, system prompt extraction, SQL injection payloads.
- `CONFLICTING_INFORMATION`: Documents with overlapping dates or pricing.
- `HALLUCINATION_TRAP`: Leading questions with false premises.
