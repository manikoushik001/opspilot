import os
import sys
import json
import asyncio

# Add backend to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["ENVIRONMENT"] = "test"
os.environ["LLM_PROVIDER"] = "mock"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models.business import Business
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.knowledge_chunk import KnowledgeChunk
from app.ai.service import AIService
from app.models.message import MessageIntent


async def run_evaluation():
    print("=" * 60)
    print("  OpsPilot AI & RAG Evaluation Suite")
    print("=" * 60)

    dataset_path = os.path.join(os.path.dirname(__file__), "dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as db:
        # Seed test business
        biz = Business(id="biz-eval-1", name="Demo Learning Center", email="info@demolearning.com")
        doc = KnowledgeDocument(
            id="doc-eval-1",
            business_id=biz.id,
            filename="pricing_and_courses.md",
            mime_type="text/markdown",
            storage_path="/tmp/pricing.md",
            status=DocumentStatus.READY,
            chunk_count=2
        )
        db.add_all([biz, doc])
        await db.flush()

        ai_svc = AIService(db)

        # Chunks
        text1 = "The Weekend Java Masterclass at Demo Learning Center is priced at $450 (or $75/week on a 6-week payment plan). It includes 36 hours of live instruction, weekend hands-on labs, and certification."
        vec1 = await ai_svc.create_embedding(text1)
        c1 = KnowledgeChunk(business_id=biz.id, document_id=doc.id, chunk_index=0, content=text1)
        c1.embedding = vec1
        c1.metadata_dict = {"filename": "pricing_and_courses.md", "page": 1}

        text2 = "Demo Learning Center is open Monday to Friday from 8:00 AM to 8:00 PM, and Saturday & Sunday from 9:00 AM to 5:00 PM. According to our refund policy, students may request a 100% refund within the first 7 days of course start. After 7 days, a pro-rated credit is available."
        vec2 = await ai_svc.create_embedding(text2)
        c2 = KnowledgeChunk(business_id=biz.id, document_id=doc.id, chunk_index=1, content=text2)
        c2.embedding = vec2
        c2.metadata_dict = {"filename": "pricing_and_courses.md", "page": 2}

        db.add_all([c1, c2])
        await db.flush()

        # Run test cases
        total = len(cases)
        intent_matches = 0
        escalation_matches = 0
        keyword_matches = 0

        print(f"\nRunning {total} test cases across categories:\n")

        for case in cases:
            cid = case["id"]
            cat = case["category"]
            msg = case["customer_message"]
            exp_intent = case["expected_intent"]
            exp_esc = case["expected_escalation"]
            exp_kw = case.get("expected_keywords", [])

            # Execute RAG Pipeline
            ans_res = await ai_svc.generate_grounded_answer(
                business_id=biz.id,
                business_name=biz.name,
                conversation_id="conv-eval",
                customer_message=msg
            )

            actual_intent = ans_res["intent"].value if hasattr(ans_res["intent"], "value") else str(ans_res["intent"])
            actual_esc = ans_res["is_escalated"]
            ans_text = ans_res["answer"]

            # Checks
            intent_ok = (actual_intent == exp_intent)
            esc_ok = (actual_esc == exp_esc)
            kw_ok = True
            if exp_kw:
                kw_ok = any(kw.lower() in ans_text.lower() for kw in exp_kw)

            if intent_ok:
                intent_matches += 1
            if esc_ok:
                escalation_matches += 1
            if kw_ok:
                keyword_matches += 1

            status_mark = "[PASS]" if (intent_ok and esc_ok and kw_ok) else "[WARN]"
            print(f"  {status_mark} [{cid}] {cat:<20} | Intent: {actual_intent:<20} | Esc: {str(actual_esc):<5} | Msg: '{msg[:40]}...'")

        print("\n" + "=" * 60)
        print("  EVALUATION RESULTS SUMMARY")
        print("=" * 60)
        print(f"  Total Test Cases:            {total}")
        print(f"  Intent Accuracy:             {(intent_matches / total) * 100:.1f}% ({intent_matches}/{total})")
        print(f"  Escalation Accuracy:         {(escalation_matches / total) * 100:.1f}% ({escalation_matches}/{total})")
        print(f"  Keyword / Grounding Match:   {(keyword_matches / total) * 100:.1f}% ({keyword_matches}/{total})")
        print("=" * 60 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_evaluation())
