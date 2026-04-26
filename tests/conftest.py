import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.models.user import RoleEnum, User

# importar models para registrar metadata
import app.models.vehicle  # noqa: F401

TEST_DATABASE_URL = settings.test_database_url or settings.database_url.replace(
    "/manage_vehicles", "/manage_vehicles_test"
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield
    engine2 = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async with engine2.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine2.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    async_session_test = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.connect() as conn:
        await conn.begin()
        async with async_session_test(bind=conn) as session:
            yield session
        await conn.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role=RoleEnum.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession) -> User:
    user = User(
        email="user@test.com",
        hashed_password=hash_password("user123"),
        role=RoleEnum.USER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token({"sub": str(admin_user.id), "role": admin_user.role})


@pytest.fixture
def user_token(regular_user: User) -> str:
    return create_access_token({"sub": str(regular_user.id), "role": regular_user.role})
