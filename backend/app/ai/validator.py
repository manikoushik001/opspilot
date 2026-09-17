import re
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.models.message import MessageIntent
from app.core.logging import get_logger

logger = get_logger("ai.validator")

# Known prompt injection signatures
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s+prompt",
    r"developer\s+mode",
    r"dan\s+mode",
    r"jailbreak",
    r"execute\s+(sql|python|bash|cmd|powershell|code)",
    r"delete\s+(database|table|records|all)",
    r"drop\s+table",
    r"select\s+\*\s+from",
    r"give\s+me\s+another\s+customer",
    r"show\s+me\s+your\s+instructions",
    r"reveal\s+your\s+prompt",
    r"bypass\s+security",
]

# Sensitive keywords that require human escalation
ESCALATION_KEYWORDS = [
    "speak to a human",
    "talk to a human",
    "real person",
    "manager",
    "lawyer",
    "legal action",
    "sue you",
    "court",
    "unacceptable",
    "terrible service",
    "scam",
    "fraud",
    "chargeback",
]


class AIValidator:
    @staticmethod
    def detect_prompt_injection(text: str) -> Tuple[bool, str]:
        """Check if customer input contains malicious prompt injection patterns."""
        lowered = text.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                logger.warning(f"Prompt injection pattern detected: {pattern}")
                return True, f"Suspicious prompt injection pattern detected: {pattern}"
        return False, ""

    @staticmethod
    def check_escalation_triggers(
        message: str,
        intent: MessageIntent,
        confidence: float,
        retrieved_sources: List[Any]
    ) -> Tuple[bool, str]:
        """
        Determine if the conversation must be escalated to HUMAN_REVIEW.
        """
        lowered = message.lower()

        # 1. Direct request for human or legal/fraud keywords
        for keyword in ESCALATION_KEYWORDS:
            if keyword in lowered:
                return True, f"Customer requested human or sensitive keyword detected: '{keyword}'"

        # 2. Refund request or Complaint always requires human review
        if intent == MessageIntent.REFUND_REQUEST:
            return True, "Refund requests require human staff verification and approval."
        
        if intent == MessageIntent.COMPLAINT:
            return True, "Customer complaint flagged for staff review."

        # 3. Low AI confidence score
        if confidence < settings.AI_CONFIDENCE_THRESHOLD:
            return True, f"AI confidence ({confidence:.2f}) below required threshold ({settings.AI_CONFIDENCE_THRESHOLD:.2f})."

        # 4. No relevant knowledge base sources found for informational questions
        if intent in [MessageIntent.COURSE_INFORMATION, MessageIntent.PRICE_QUERY, MessageIntent.GENERAL_INFORMATION]:
            if not retrieved_sources:
                return True, "No verified knowledge base records matched the inquiry."

        return False, ""

    @staticmethod
    def validate_grounding(
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Validate that the generated answer does not claim ungrounded facts.
        """
        if not sources and len(answer) > 100:
            # If no sources were retrieved but the answer is long and detailed, suspicious hallucination
            return False, "Answer generated without supporting source documents."
        return True, ""
