import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.database import engine, async_session, init_db
from src.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    # Re-create tables for each test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_and_login(client: AsyncClient, email: str, name: str = "Test User") -> dict:
    await client.post("/api/auth/register", json={
        "name": name,
        "email": email,
        "password": "password123",
    })
    response = await client.post("/api/auth/login", json={
        "email": email,
        "password": "password123",
    })
    return response.json()


async def get_auth_header(client: AsyncClient, email: str, name: str = "Test User") -> dict:
    data = await register_and_login(client, email, name)
    return {"Authorization": f"Bearer {data['access_token']}"}


async def make_admin(client: AsyncClient, email: str = "admin@test.com") -> dict:
    # Register
    await client.post("/api/auth/register", json={
        "name": "Admin",
        "email": email,
        "password": "password123",
    })
    # Login
    login_resp = await client.post("/api/auth/login", json={
        "email": email,
        "password": "password123",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from src.database import async_session
    from src.models.user import User
    from sqlalchemy import select, update

    async with async_session() as session:
        await session.execute(
            update(User).where(User.email == email).values(role="admin")
        )
        await session.commit()

    # Re-login to get token with updated role
    login_resp = await client.post("/api/auth/login", json={
        "email": email,
        "password": "password123",
    })
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
