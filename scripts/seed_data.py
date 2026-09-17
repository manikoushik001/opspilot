import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

# Add backend to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import select
from app.core.database import async_engine, AsyncSessionLocal, Base
from app.models.user import User
from app.models.business import Business
from app.models.membership import BusinessMember, MemberRole
from app.models.customer import Customer, CustomerStatus
from app.models.conversation import Conversation, ConversationStatus, ConversationPriority
from app.models.message import Message, SenderType, MessageIntent
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.followup import Followup, FollowupStatus
from app.models.ai_interaction import AIInteraction
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash
from app.ai.chunking import chunk_text
from app.ai.service import AIService


async def seed_database():
    print("=" * 60)
    print("  OpsPilot - Seeding Demo Learning Center (DEMO DATA)")
    print("=" * 60)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing_biz = await db.execute(select(Business).where(Business.name == "Demo Learning Center"))
        if existing_biz.scalar_one_or_none():
            print("Database already contains 'Demo Learning Center' data. Skipping seed.")
            return

        now = datetime.now(timezone.utc)

        # 1. Create Demo Business
        business = Business(
            id="biz-demo-001",
            name="Demo Learning Center",
            description="Leading vocational tech academy providing high-impact software engineering and AI courses. [DEMO DATA]",
            industry="Education & Training",
            email="contact@demolearning.com",
            phone="(512) 555-0199",
            timezone="America/Chicago"
        )
        db.add(business)
        await db.flush()

        # 2. Create Users (Owner & Staff)
        owner_user = User(
            id="user-owner-001",
            email="owner@demolearning.com",
            full_name="Sarah Jenkins (Owner)",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        staff_user = User(
            id="user-staff-001",
            email="staff@demolearning.com",
            full_name="Alex Rivera (Operations Staff)",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add_all([owner_user, staff_user])
        await db.flush()

        # 3. Create Memberships
        mem_owner = BusinessMember(business_id=business.id, user_id=owner_user.id, role=MemberRole.OWNER)
        mem_staff = BusinessMember(business_id=business.id, user_id=staff_user.id, role=MemberRole.STAFF)
        db.add_all([mem_owner, mem_staff])
        await db.flush()

        # 4. Ingest Demo Knowledge Documents
        knowledge_dir = os.path.join(os.path.dirname(__file__), "demo_knowledge")
        knowledge_files = [
            ("courses.md", "Course Catalog"),
            ("pricing.md", "Tuition & Pricing Policy"),
            ("faq.md", "Frequently Asked Questions"),
            ("refund-policy.md", "Official Refund Policy"),
            ("timings.md", "Operating Hours & Schedules"),
        ]

        ai_svc = AIService(db)

        for filename, doc_title in knowledge_files:
            filepath = os.path.join(knowledge_dir, filename)
            if not os.path.exists(filepath):
                continue
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            doc = KnowledgeDocument(
                business_id=business.id,
                filename=filename,
                mime_type="text/markdown",
                storage_path=filepath,
                status=DocumentStatus.READY
            )
            db.add(doc)
            await db.flush()

            chunks = chunk_text(content, chunk_size=450, chunk_overlap=50, metadata={"filename": filename, "title": doc_title})
            chunk_count = 0
            for chunk_data in chunks:
                vec = await ai_svc.create_embedding(chunk_data["content"])
                kc = KnowledgeChunk(
                    business_id=business.id,
                    document_id=doc.id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"]
                )
                kc.embedding = vec
                kc.metadata_dict = chunk_data["metadata"]
                db.add(kc)
                chunk_count += 1

            doc.chunk_count = chunk_count
            print(f"  [Knowledge] Indexed {filename} ({chunk_count} chunks)")

        await db.flush()

        # 5. Create 8 Demo Customers
        customers_data = [
            {"id": "cust-001", "name": "Emily Watson", "email": "emily.w@example.com", "phone": "(512) 555-1011", "status": CustomerStatus.ACTIVE, "notes": "Enrolled in Weekend Java batch. Excellent lab participation."},
            {"id": "cust-002", "name": "David Kim", "email": "david.k@example.com", "phone": "(512) 555-1022", "status": CustomerStatus.FOLLOW_UP, "notes": "Interested in Python for Data Science. Evaluating weekend vs weekday schedule."},
            {"id": "cust-003", "name": "Jessica Taylor", "email": "jessica.t@example.com", "phone": "(512) 555-1033", "status": CustomerStatus.NEW, "notes": "Inquired via website form regarding UI/UX cohort."},
            {"id": "cust-004", "name": "Marcus Vance", "email": "marcus.v@example.com", "phone": "(512) 555-1044", "status": CustomerStatus.RESOLVED, "notes": "Completed Web Dev enrollment fee payment."},
            {"id": "cust-005", "name": "Rachel Adams", "email": "rachel.a@example.com", "phone": "(512) 555-1055", "status": CustomerStatus.ACTIVE, "notes": "Student discount verified."},
            {"id": "cust-006", "name": "Brian O'Connor", "email": "brian.o@example.com", "phone": "(512) 555-1066", "status": CustomerStatus.FOLLOW_UP, "notes": "Requested follow-up call on Friday regarding tuition installment options."},
            {"id": "cust-007", "name": "Sophia Martinez", "email": "sophia.m@example.com", "phone": "(512) 555-1077", "status": CustomerStatus.NEW, "notes": "Asked about classroom WiFi and lab hardware."},
            {"id": "cust-008", "name": "Daniel Lee", "email": "daniel.l@example.com", "phone": "(512) 555-1088", "status": CustomerStatus.INACTIVE, "notes": "Postponed enrollment to summer cohort."},
        ]

        customers = []
        for cd in customers_data:
            c = Customer(
                id=cd["id"],
                business_id=business.id,
                name=cd["name"],
                email=cd["email"],
                phone=cd["phone"],
                status=cd["status"],
                notes=cd["notes"]
            )
            db.add(c)
            customers.append(c)
        await db.flush()
        print(f"  [Customers] Created {len(customers)} demo customer profiles")

        # 6. Create Demo Conversations & Messages
        conversations_config = [
            {
                "id": "conv-001",
                "customer": customers[0],
                "status": ConversationStatus.OPEN,
                "priority": ConversationPriority.MEDIUM,
                "messages": [
                    (SenderType.CUSTOMER, "Hi there, what is the fee for the weekend Java course?", MessageIntent.PRICE_QUERY, 0.95),
                    (SenderType.AI, "The Weekend Java Masterclass at Demo Learning Center is priced at $450 (or $75/week on a 6-week payment plan). It includes 36 hours of live instruction, weekend hands-on labs, and certification.", MessageIntent.PRICE_QUERY, 0.96),
                    (SenderType.CUSTOMER, "Great! Are classes held on both Saturday and Sunday?", MessageIntent.GENERAL_INFORMATION, 0.94),
                    (SenderType.STAFF, "Yes Emily! Live lectures run Saturdays and Sundays from 10:00 AM to 1:00 PM.", None, None)
                ]
            },
            {
                "id": "conv-002",
                "customer": customers[1],
                "status": ConversationStatus.WAITING,
                "priority": ConversationPriority.MEDIUM,
                "messages": [
                    (SenderType.CUSTOMER, "Do you have evening timings for the Python Data Science course?", MessageIntent.GENERAL_INFORMATION, 0.93),
                    (SenderType.AI, "Yes! Python for Data Science & AI runs on Tuesdays and Thursdays from 6:30 PM to 9:00 PM.", MessageIntent.GENERAL_INFORMATION, 0.95),
                    (SenderType.CUSTOMER, "Thanks, I will think about it and decide tomorrow.", MessageIntent.FOLLOW_UP, 0.92)
                ]
            },
            {
                "id": "conv-003",
                "customer": customers[2],
                "status": ConversationStatus.HUMAN_REVIEW,
                "priority": ConversationPriority.HIGH,
                "messages": [
                    (SenderType.CUSTOMER, "I enrolled last week but need to cancel. I would like a refund please.", MessageIntent.REFUND_REQUEST, 0.96),
                    (SenderType.AI, "According to our refund policy, students may request a 100% refund within the first 7 days of course start. I have escalated this request to our operations team for priority review.", MessageIntent.REFUND_REQUEST, 0.95)
                ]
            },
            {
                "id": "conv-004",
                "customer": customers[3],
                "status": ConversationStatus.RESOLVED,
                "priority": ConversationPriority.LOW,
                "messages": [
                    (SenderType.CUSTOMER, "What is the center address in Austin?", MessageIntent.GENERAL_INFORMATION, 0.94),
                    (SenderType.AI, "Our campus is located at 450 Innovation Parkway, Suite 300, Tech District, Austin, TX 78701.", MessageIntent.GENERAL_INFORMATION, 0.96),
                    (SenderType.CUSTOMER, "Thank you, that was very helpful!", MessageIntent.OTHER, 0.90),
                    (SenderType.STAFF, "You're welcome! Feel free to visit anytime during open hours.", None, None)
                ]
            },
            {
                "id": "conv-005",
                "customer": customers[5],
                "status": ConversationStatus.OPEN,
                "priority": ConversationPriority.HIGH,
                "messages": [
                    (SenderType.CUSTOMER, "Can I schedule a quick 15-minute campus tour tomorrow?", MessageIntent.APPOINTMENT_REQUEST, 0.92),
                    (SenderType.AI, "I would be happy to help arrange a campus tour! Our team is available between 9:00 AM and 5:00 PM. A staff member will confirm your preferred time slot shortly.", MessageIntent.APPOINTMENT_REQUEST, 0.92)
                ]
            }
        ]

        for cdata in conversations_config:
            conv = Conversation(
                id=cdata["id"],
                business_id=business.id,
                customer_id=cdata["customer"].id,
                status=cdata["status"],
                priority=cdata["priority"],
                assigned_to=staff_user.id
            )
            db.add(conv)
            await db.flush()

            for sender_type, content, intent, conf in cdata["messages"]:
                sender_id = cdata["customer"].id if sender_type == SenderType.CUSTOMER else (staff_user.id if sender_type == SenderType.STAFF else "ai")
                msg = Message(
                    conversation_id=conv.id,
                    sender_type=sender_type,
                    sender_id=sender_id,
                    content=content,
                    intent=intent,
                    ai_confidence=conf
                )
                db.add(msg)

        await db.flush()
        print(f"  [Conversations] Created {len(conversations_config)} rich conversation threads with messages")

        # 7. Create Follow-up Tasks
        followups_data = [
            {"cust": customers[1], "title": "Check in with David regarding Python batch decision", "due_delta": 1, "status": FollowupStatus.PENDING},
            {"cust": customers[5], "title": "Confirm 15-minute campus tour slot with Brian", "due_delta": 0, "status": FollowupStatus.PENDING},
            {"cust": customers[2], "title": "Process 100% tuition refund approval for Jessica", "due_delta": -1, "status": FollowupStatus.PENDING},
            {"cust": customers[0], "title": "Send Java IDE setup guide PDF to Emily", "due_delta": -2, "status": FollowupStatus.COMPLETED},
        ]

        for fdata in followups_data:
            due_at = now + timedelta(days=fdata["due_delta"])
            f = Followup(
                business_id=business.id,
                customer_id=fdata["cust"].id,
                assigned_to=staff_user.id,
                title=fdata["title"],
                due_at=due_at,
                status=fdata["status"],
                completed_at=now if fdata["status"] == FollowupStatus.COMPLETED else None
            )
            db.add(f)
        await db.flush()
        print("  [Followups] Created 4 initial operational follow-ups (including 1 overdue task)")

        # 8. Create Audit Logs
        audit_records = [
            {"action": "BUSINESS_INITIALIZED", "type": "business", "id": business.id, "user": owner_user.id},
            {"action": "KNOWLEDGE_BATCH_INDEXED", "type": "knowledge", "id": "docs", "user": owner_user.id},
            {"action": "AI_SYSTEM_CALIBRATED", "type": "ai_config", "id": "rag_pipeline", "user": owner_user.id},
        ]
        for a in audit_records:
            log = AuditLog(
                business_id=business.id,
                user_id=a["user"],
                action=a["action"],
                resource_type=a["type"],
                resource_id=a["id"]
            )
            log.metadata_dict = {"source": "seed_data_script", "status": "verified"}
            db.add(log)

        await db.commit()
        print("=" * 60)
        print("  SEEDING COMPLETE!")
        print(f"  Owner Login:  {owner_user.email}  (password: password123)")
        print(f"  Staff Login:  {staff_user.email}  (password: password123)")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
