import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.service import AIService
from app.models.message import MessageIntent
from app.models.ai_action import ActionType

@pytest.mark.asyncio
async def test_all_eight_intents_recognized(test_db: AsyncSession):
    """Verify that AIService classifies all 8 supported intent types correctly."""
    ai_service = AIService(test_db)
    
    test_cases = [
        ("What courses and syllabus do you offer for web development?", MessageIntent.COURSE_INFORMATION),
        ("How much does the data science bootcamp cost? What are the fees?", MessageIntent.PRICE_QUERY),
        ("Can I book an appointment or schedule a visit to the campus?", MessageIntent.APPOINTMENT_REQUEST),
        ("Your instructor was 45 minutes late and this service is terrible", MessageIntent.COMPLAINT),
        ("I want to cancel my enrollment and request a refund immediately", MessageIntent.REFUND_REQUEST),
        ("Following up on my previous message from yesterday", MessageIntent.FOLLOW_UP),
        ("What are your operating hours and where are you located?", MessageIntent.GENERAL_INFORMATION),
        ("Hello, can you help me with a random question?", MessageIntent.OTHER),
    ]
    
    for message, expected_intent in test_cases:
        classification = await ai_service.classify_intent(
            text=message,
            business_id="test-biz"
        )
        assert "intent" in classification
        assert isinstance(classification["intent"], MessageIntent)
        assert 0.0 <= classification["confidence"] <= 1.0
        assert classification["intent"] == expected_intent, f"Expected {expected_intent} for '{message}', got {classification['intent']}"


@pytest.mark.asyncio
async def test_action_suggestion_rules(test_db: AsyncSession):
    """Ensure LLM provider suggests controlled actions based on intent."""
    ai_service = AIService(test_db)
    
    # Delayed decision should suggest CREATE_FOLLOWUP
    suggestion = await ai_service.provider.suggest_action(
        message="I need to think about it and will decide tomorrow",
        intent="FOLLOW_UP"
    )
    
    assert suggestion["action"] == "CREATE_FOLLOWUP"
    assert "reason" in suggestion
    assert isinstance(suggestion["payload"], dict)
