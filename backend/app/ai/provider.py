import os
import re
import json
import math
import hashlib
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import get_logger
from app.ai.prompts import INTENT_CLASSIFICATION_SYSTEM_PROMPT, RAG_ANSWER_SYSTEM_PROMPT, ACTION_SUGGESTION_SYSTEM_PROMPT
from app.ai.validator import AIValidator

logger = get_logger("ai.provider")


class LLMProvider(ABC):
    @abstractmethod
    async def create_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_rag_answer(
        self,
        message: str,
        context_chunks: List[Dict[str, Any]],
        business_name: str
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def suggest_action(
        self,
        message: str,
        intent: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        pass


class MockLLMProvider(LLMProvider):
    """
    Deterministic, highly-capable offline provider for testing, evaluation, and zero-dependency local demos.
    Emulates accurate semantic embedding vectors and domain classification for 'Demo Learning Center'.
    """

    async def create_embedding(self, text: str) -> List[float]:
        # Generate a deterministic normalized 1536-dim semantic vector with concept clustering
        dim = settings.EMBEDDING_DIM
        vec = [0.0] * dim
        tokens = re.findall(r'\b\w+\b', text.lower())
        if not tokens:
            return vec

        # Concept clusters
        clusters = {
            "course": (0, 100, ["java", "python", "javascript", "react", "fullstack", "programming", "syllabus", "masterclass", "curriculum"]),
            "price": (100, 200, ["fee", "fees", "price", "pricing", "cost", "priced", "tuition", "450", "75", "dollar", "payment", "plan"]),
            "refund": (200, 300, ["refund", "refunds", "cancel", "cancellation", "credit", "money", "policy", "return"]),
            "timing": (300, 400, ["weekend", "saturday", "sunday", "hours", "timings", "timing", "open", "time", "schedule", "pm", "am"]),
            "appointment": (400, 500, ["appointment", "tour", "visit", "book", "meet", "demo"]),
        }

        # Boost matching concept dimensions
        for cname, (start_idx, end_idx, kw_list) in clusters.items():
            match_count = sum(1 for tok in tokens if any(kw in tok or tok in kw for kw in kw_list))
            if match_count > 0:
                boost = match_count * 8.0
                for i in range(start_idx, end_idx):
                    vec[i] += boost / (end_idx - start_idx)

        # Token hashing for general vocabulary
        stopwords = {"what", "is", "the", "for", "in", "at", "and", "a", "an", "of", "to", "on", "it", "our", "do", "you"}
        for token in tokens:
            if token in stopwords:
                continue
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = 500 + (h % (dim - 500))
            vec[idx] += 0.2

        # Normalize vector to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def classify_intent(self, message: str) -> Dict[str, Any]:
        is_injection, reason = AIValidator.detect_prompt_injection(message)
        if is_injection:
            return {
                "intent": "OTHER",
                "confidence": 0.99,
                "reasoning": f"Prompt injection suspected: {reason}",
                "is_injection_suspected": True,
                "requires_human_escalation": True
            }

        msg = message.lower()
        if any(w in msg for w in ["refund", "money back", "cancel enrolment", "fee return", "cancellation"]):
            return {
                "intent": "REFUND_REQUEST",
                "confidence": 0.96,
                "reasoning": "Customer is asking about refund or cancellation.",
                "is_injection_suspected": False,
                "requires_human_escalation": True
            }
        elif any(w in msg for w in ["fee", "price", "cost", "pricing", "tuition", "how much"]):
            return {
                "intent": "PRICE_QUERY",
                "confidence": 0.95,
                "reasoning": "Inquiry regarding course fees and tuition pricing.",
                "is_injection_suspected": False,
                "requires_human_escalation": False
            }
        elif any(w in msg for w in ["java", "python", "course", "curriculum", "syllabus", "learn", "class", "teach", "prerequisite"]):
            return {
                "intent": "COURSE_INFORMATION",
                "confidence": 0.94,
                "reasoning": "Inquiry regarding course syllabus and offerings.",
                "is_injection_suspected": False,
                "requires_human_escalation": False
            }
        elif any(w in msg for w in ["appointment", "book", "schedule", "visit", "tour", "demo class", "meet"]):
            return {
                "intent": "APPOINTMENT_REQUEST",
                "confidence": 0.92,
                "reasoning": "Customer wants to schedule a visit or demo appointment.",
                "is_injection_suspected": False,
                "requires_human_escalation": False
            }
        elif any(w in msg for w in ["complaint", "unhappy", "terrible", "bad", "angry", "poor", "issue", "problem"]):
            return {
                "intent": "COMPLAINT",
                "confidence": 0.93,
                "reasoning": "Customer expressing dissatisfaction or issue.",
                "is_injection_suspected": False,
                "requires_human_escalation": True
            }
        elif any(w in msg for w in ["decide tomorrow", "think about it", "let you know", "follow up", "following up", "follow-up", "next week", "later"]):
            return {
                "intent": "FOLLOW_UP",
                "confidence": 0.91,
                "reasoning": "Customer indicates delayed decision or need for follow-up.",
                "is_injection_suspected": False,
                "requires_human_escalation": False
            }
        elif any(w in msg for w in ["hours", "timings", "timing", "open", "address", "location", "contact", "wifi", "where"]):
            return {
                "intent": "GENERAL_INFORMATION",
                "confidence": 0.93,
                "reasoning": "General operational inquiry.",
                "is_injection_suspected": False,
                "requires_human_escalation": False
            }
        else:
            return {
                "intent": "OTHER",
                "confidence": 0.70,
                "reasoning": "General conversation or ambiguous intent.",
                "is_injection_suspected": False,
                "requires_human_escalation": False
            }

    async def generate_rag_answer(
        self,
        message: str,
        context_chunks: List[Dict[str, Any]],
        business_name: str
    ) -> Dict[str, Any]:
        is_injection, _ = AIValidator.detect_prompt_injection(message)
        if is_injection:
            return {
                "answer": "Your request contains prohibited operational commands. For assistance, our human staff will reach out to you.",
                "confidence": 0.99,
                "sources_used_indexes": [],
                "is_escalated": True,
                "escalation_reason": "Security: Prompt injection attempt detected."
            }

        if not context_chunks:
            return {
                "answer": f"I cannot find verified information regarding this in the {business_name} knowledge base. I have forwarded your question to our staff for personal assistance.",
                "confidence": 0.50,
                "sources_used_indexes": [],
                "is_escalated": True,
                "escalation_reason": "No relevant knowledge sources found in business documents."
            }

        # Synthesize grounded answer from matching chunks
        combined_text = "\n\n".join([c.get("content", "") for c in context_chunks])
        msg_lower = message.lower()

        # Handle specific domain matches
        if "java" in msg_lower and ("fee" in msg_lower or "cost" in msg_lower or "price" in msg_lower or "weekend" in msg_lower):
            answer = "The Weekend Java Masterclass at Demo Learning Center is priced at $450 (or $75/week on a 6-week payment plan). It includes 36 hours of live instruction, weekend hands-on labs, and certification."
            used_indexes = [c.get("chunk_index", 0) for c in context_chunks[:2]]
            return {
                "answer": answer,
                "confidence": 0.96,
                "sources_used_indexes": used_indexes,
                "is_escalated": False,
                "escalation_reason": None
            }
        elif "refund" in msg_lower:
            answer = "According to our refund policy, students may request a 100% refund within the first 7 days of course start. After 7 days, a pro-rated credit is available. All refund requests are reviewed by our operations team."
            used_indexes = [c.get("chunk_index", 0) for c in context_chunks[:1]]
            return {
                "answer": answer,
                "confidence": 0.95,
                "sources_used_indexes": used_indexes,
                "is_escalated": True,
                "escalation_reason": "Policy requires staff confirmation for refund requests."
            }
        elif "timing" in msg_lower or "hours" in msg_lower or "open" in msg_lower:
            answer = "Demo Learning Center is open Monday to Friday from 8:00 AM to 8:00 PM, and Saturday & Sunday from 9:00 AM to 5:00 PM."
            return {
                "answer": answer,
                "confidence": 0.95,
                "sources_used_indexes": [c.get("chunk_index", 0) for c in context_chunks[:1]],
                "is_escalated": False,
                "escalation_reason": None
            }
        else:
            # Fallback grounded answer from highest scoring chunk
            top_chunk = context_chunks[0].get("content", "").strip()
            first_sentence = top_chunk.split("\n")[0] if top_chunk else "Here is the relevant information."
            return {
                "answer": f"Based on our records: {first_sentence}",
                "confidence": 0.88,
                "sources_used_indexes": [context_chunks[0].get("chunk_index", 0)],
                "is_escalated": False,
                "escalation_reason": None
            }

    async def suggest_action(
        self,
        message: str,
        intent: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        msg_lower = message.lower()
        if any(phrase in msg_lower for phrase in ["decide tomorrow", "think about it", "follow up", "call me tomorrow", "next week"]):
            return {
                "action": "CREATE_FOLLOWUP",
                "confidence": 0.93,
                "reason": "Customer requested time to decide and indicated follow-up timeframe.",
                "payload": {
                    "title": "Check in regarding course enrollment decision",
                    "due_days": 1,
                    "description": f"Customer mentioned: '{message}'. Follow up regarding decision."
                }
            }
        elif intent == "REFUND_REQUEST" or "refund" in msg_lower or intent == "COMPLAINT":
            return {
                "action": "ESCALATE_TO_HUMAN",
                "confidence": 0.95,
                "reason": f"High-priority operational issue ({intent}) requires human intervention.",
                "payload": {
                    "new_status": "HUMAN_REVIEW"
                }
            }
        elif "enroll" in msg_lower or "sign up" in msg_lower or "ready to register" in msg_lower:
            return {
                "action": "UPDATE_CUSTOMER_STATUS",
                "confidence": 0.90,
                "reason": "Customer expressed readiness to enroll.",
                "payload": {
                    "new_status": "ACTIVE"
                }
            }
        return {
            "action": "NONE",
            "confidence": 0.90,
            "reason": "Standard inquiry without explicit operational action trigger.",
            "payload": {}
        }


class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1"

    async def create_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            return await MockLLMProvider().create_embedding(text)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": text, "model": self.embedding_model}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    async def classify_intent(self, message: str) -> Dict[str, Any]:
        if not self.api_key:
            return await MockLLMProvider().classify_intent(message)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": INTENT_CLASSIFICATION_SYSTEM_PROMPT},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.0
                }
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)

    async def generate_rag_answer(
        self,
        message: str,
        context_chunks: List[Dict[str, Any]],
        business_name: str
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await MockLLMProvider().generate_rag_answer(message, context_chunks, business_name)
        
        context_str = "\n\n---\n\n".join([
            f"[Chunk {c.get('chunk_index', idx)} | File: {c.get('filename', 'doc')}]: {c.get('content', '')}"
            for idx, c in enumerate(context_chunks)
        ])
        system_prompt = RAG_ANSWER_SYSTEM_PROMPT.format(business_name=business_name, context=context_str, message=message)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "temperature": 0.1
                }
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)

    async def suggest_action(
        self,
        message: str,
        intent: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        if not self.api_key:
            return await MockLLMProvider().suggest_action(message, intent, conversation_history)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": ACTION_SUGGESTION_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Intent: {intent}\nCustomer Message: {message}"}
                    ],
                    "temperature": 0.0
                }
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)


def get_llm_provider() -> LLMProvider:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai" and settings.LLM_API_KEY:
        return OpenAILLMProvider()
    return MockLLMProvider()
