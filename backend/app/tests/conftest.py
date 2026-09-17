import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-execution-32-chars-long"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["LLM_PROVIDER"] = "mock"

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.business import Business
from app.models.membership import BusinessMember, MemberRole
from app.models.customer import Customer, CustomerStatus
from app.core.security import get_password_hash, create_access_token


@pytest_asyncio.fixture(scope="function")
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db():
        yield test_db

    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def tenant_a_data(test_db: AsyncSession):
    """Sets up Tenant A: Business A, Owner A, Staff A, Customer A."""
    biz_a = Business(id="biz-a-111", name="Business A Learning Center", email="owner-a@test.com")
    user_owner_a = User(
        id="user-owner-a-111",
        email="owner-a@test.com",
        full_name="Owner A",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    user_staff_a = User(
        id="user-staff-a-111",
        email="staff-a@test.com",
        full_name="Staff A",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    mem_owner_a = BusinessMember(business_id=biz_a.id, user_id=user_owner_a.id, role=MemberRole.OWNER)
    mem_staff_a = BusinessMember(business_id=biz_a.id, user_id=user_staff_a.id, role=MemberRole.STAFF)
    
    customer_a = Customer(
        id="cust-a-111",
        business_id=biz_a.id,
        name="Alice TenantA",
        email="alice@tenanta.com",
        phone="555-0101",
        status=CustomerStatus.ACTIVE
    )

    test_db.add_all([biz_a, user_owner_a, user_staff_a, mem_owner_a, mem_staff_a, customer_a])
    await test_db.commit()

    token_owner_a = create_access_token(user_owner_a.id)
    token_staff_a = create_access_token(user_staff_a.id)

    return {
        "business": biz_a,
        "owner": user_owner_a,
        "staff": user_staff_a,
        "customer": customer_a,
        "owner_token": token_owner_a,
        "staff_token": token_staff_a,
        "headers_owner": {"Authorization": f"Bearer {token_owner_a}", "X-Business-ID": biz_a.id},
        "headers_staff": {"Authorization": f"Bearer {token_staff_a}", "X-Business-ID": biz_a.id},
    }


@pytest_asyncio.fixture(scope="function")
async def tenant_b_data(test_db: AsyncSession):
    """Sets up Tenant B: Business B, Owner B, Customer B."""
    biz_b = Business(id="biz-b-222", name="Business B Academy", email="owner-b@test.com")
    user_owner_b = User(
        id="user-owner-b-222",
        email="owner-b@test.com",
        full_name="Owner B",
        hashed_password=get_password_hash("password123"),
        is_active=True
    )
    mem_owner_b = BusinessMember(business_id=biz_b.id, user_id=user_owner_b.id, role=MemberRole.OWNER)
    customer_b = Customer(
        id="cust-b-222",
        business_id=biz_b.id,
        name="Bob TenantB",
        email="bob@tenantb.com",
        phone="555-0202",
        status=CustomerStatus.NEW
    )

    test_db.add_all([biz_b, user_owner_b, mem_owner_b, customer_b])
    await test_db.commit()

    token_owner_b = create_access_token(user_owner_b.id)

    return {
        "business": biz_b,
        "owner": user_owner_b,
        "customer": customer_b,
        "owner_token": token_owner_b,
        "headers_owner": {"Authorization": f"Bearer {token_owner_b}", "X-Business-ID": biz_b.id},
    }
