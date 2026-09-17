import time
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.message import MessageIntent
from app.models.ai_interaction import AIInteraction
from app.models.ai_action import AIAction, ActionType, ActionExecutionStatus
from app.ai.provider import get_llm_provider
from app.ai.validator import AIValidator

logger = get_logger("ai.service")


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = get_llm_provider()

    async def classify_intent(
        self,
        text: str,
        business_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        raw_result = await self.provider.classify_intent(text)
        latency_ms = int((time.time() - start_time) * 1000)

        intent_str = raw_result.get("intent", "OTHER")
        try:
            intent_enum = MessageIntent(intent_str)
        except ValueError:
            intent_enum = MessageIntent.OTHER

        confidence = float(raw_result.get("confidence", 0.7))
        is_injection = bool(raw_result.get("is_injection_suspected", False))
        requires_escalation = bool(raw_result.get("requires_human_escalation", False))

        # Log AI interaction
        interaction = AIInteraction(
            business_id=business_id,
            conversation_id=conversation_id,
            model=settings.LLM_MODEL,
            operation="classify_intent",
            confidence=confidence,
            retrieval_count=0,
            latency_ms=latency_ms,
            success=True,
        )
        self.db.add(interaction)

        return {
            "intent": intent_enum,
            "confidence": confidence,
            "model": settings.LLM_MODEL,
            "is_injection_suspected": is_injection,
            "requires_human_escalation": requires_escalation,
            "reasoning": raw_result.get("reasoning", "")
        }

    async def create_embedding(self, text: str) -> List[float]:
        return await self.provider.create_embedding(text)

    async def retrieve_context(
        self,
        business_id: str,
        query: str,
        top_k: int = 4,
        similarity_threshold: float = 0.60
    ) -> List[Dict[str, Any]]:
        """
        Tenant-isolated vector retrieval.
        Searches ONLY chunks belonging to the specified business_id.
        """
        query_vector = await self.create_embedding(query)

        # Retrieve ready documents for this tenant
        doc_stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.business_id == business_id,
            KnowledgeDocument.status == DocumentStatus.READY
        )
        doc_res = await self.db.execute(doc_stmt)
        docs = {doc.id: doc.filename for doc in doc_res.scalars().all()}

        if not docs:
            return []

        chunk_stmt = select(KnowledgeChunk).where(
            KnowledgeChunk.business_id == business_id,
            KnowledgeChunk.document_id.in_(list(docs.keys()))
        )
        chunk_res = await self.db.execute(chunk_stmt)
        chunks = chunk_res.scalars().all()

        scored_chunks: List[Dict[str, Any]] = []
        for chunk in chunks:
            chunk_vec = chunk.embedding
            if not chunk_vec:
                continue
            sim = cosine_similarity(query_vector, chunk_vec)
            if sim >= similarity_threshold:
                scored_chunks.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": docs.get(chunk.document_id, "unknown"),
                    "content": chunk.content,
                    "similarity_score": round(sim, 4),
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata_dict
                })

        # Sort by similarity descending and take top_k
        scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_chunks[:top_k]

    async def generate_grounded_answer(
        self,
        business_id: str,
        business_name: str,
        conversation_id: str,
        customer_message: str,
        intent: Optional[MessageIntent] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Intent classification if not provided
        if not intent:
            class_res = await self.classify_intent(customer_message, business_id, conversation_id)
            intent = class_res["intent"]
            intent_confidence = class_res["confidence"]
        else:
            intent_confidence = 0.90

        # 2. Check prompt injection
        is_injection, injection_reason = AIValidator.detect_prompt_injection(customer_message)
        if is_injection:
            return {
                "answer": "Your request contains prohibited instructions. A staff member has been alerted to assist you directly.",
                "confidence": 0.99,
                "intent": intent,
                "sources_used": [],
                "is_escalated": True,
                "escalation_reason": injection_reason,
                "suggested_action": ActionType.ESCALATE_TO_HUMAN,
                "action_payload": {"reason": injection_reason},
                "latency_ms": int((time.time() - start_time) * 1000)
            }

        # 3. Vector retrieval strictly scoped to business_id
        retrieved_chunks = await self.retrieve_context(
            business_id=business_id,
            query=customer_message,
            top_k=settings.RAG_TOP_K,
            similarity_threshold=settings.RAG_SIMILARITY_THRESHOLD
        )

        # 4. Check escalation triggers
        must_escalate, esc_reason = AIValidator.check_escalation_triggers(
            message=customer_message,
            intent=intent,
            confidence=intent_confidence,
            retrieved_sources=retrieved_chunks
        )

        # 5. Generate LLM answer with context
        raw_answer = await self.provider.generate_rag_answer(
            message=customer_message,
            context_chunks=retrieved_chunks,
            business_name=business_name
        )

        answer_text = raw_answer.get("answer", "")
        answer_confidence = float(raw_answer.get("confidence", 0.85))
        final_is_escalated = must_escalate or raw_answer.get("is_escalated", False)
        final_esc_reason = esc_reason or raw_answer.get("escalation_reason")

        # 6. Suggest action
        suggested_action_res = await self.provider.suggest_action(
            message=customer_message,
            intent=intent.value if isinstance(intent, MessageIntent) else str(intent)
        )
        action_type_str = suggested_action_res.get("action", "NONE")
        try:
            suggested_action_enum = ActionType(action_type_str)
        except ValueError:
            suggested_action_enum = ActionType.NONE

        latency_ms = int((time.time() - start_time) * 1000)

        # 7. Record AI Interaction
        interaction = AIInteraction(
            business_id=business_id,
            conversation_id=conversation_id,
            model=settings.LLM_MODEL,
            operation="rag_answer",
            confidence=answer_confidence,
            retrieval_count=len(retrieved_chunks),
            latency_ms=latency_ms,
            success=True
        )
        self.db.add(interaction)

        # 8. Record AI Action Proposal if suggested
        if suggested_action_enum != ActionType.NONE:
            ai_act = AIAction(
                business_id=business_id,
                conversation_id=conversation_id,
                action_type=suggested_action_enum,
                status=ActionExecutionStatus.PROPOSED,
                reason=suggested_action_res.get("reason"),
                payload_json=None
            )
            ai_act.payload = suggested_action_res.get("payload", {})
            self.db.add(ai_act)

        return {
            "answer": answer_text,
            "confidence": answer_confidence,
            "intent": intent,
            "sources_used": [
                {
                    "chunk_id": c["chunk_id"],
                    "document_id": c["document_id"],
                    "filename": c["filename"],
                    "content": c["content"],
                    "similarity_score": c["similarity_score"],
                    "chunk_index": c["chunk_index"],
                    "page": c["metadata"].get("page")
                }
                for c in retrieved_chunks
            ],
            "is_escalated": final_is_escalated,
            "escalation_reason": final_esc_reason,
            "suggested_action": suggested_action_enum,
            "action_payload": suggested_action_res.get("payload", {}),
            "latency_ms": latency_ms
        }
