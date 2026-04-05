"""Tests for RBAC (Role-Based Access Control)."""

import pytest
from httpx import AsyncClient
from tests.conftest import get_auth_header, make_admin


@pytest.mark.asyncio
async def test_viewer_cannot_create_record(client: AsyncClient):
    """Viewer should get 403 when trying to create a record."""
    headers = await get_auth_header(client, "viewer@test.com")
    response = await client.post("/api/records", json={
        "amount": 100,
        "type": "income",
        "category": "salary",
        "date": "2026-04-01",
    }, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_access_analytics(client: AsyncClient):
    """Viewer should get 403 when trying to access dashboard."""
    headers = await get_auth_header(client, "viewer@test.com")
    response = await client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_viewer_can_read_records(client: AsyncClient):
    """Viewer should be able to list records."""
    headers = await get_auth_header(client, "viewer@test.com")
    response = await client.get("/api/records", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyst_can_access_analytics(client: AsyncClient):
    """Analyst should be able to access dashboard analytics."""
    # Create analyst user
    await client.post("/api/auth/register", json={
        "name": "Analyst",
        "email": "analyst@test.com",
        "password": "password123",
    })

    # Promote to analyst via DB
    from src.database import async_session
    from src.models.user import User
    from sqlalchemy import update
    async with async_session() as session:
        await session.execute(
            update(User).where(User.email == "analyst@test.com").values(role="analyst")
        )
        await session.commit()

    # Login with updated role
    login_resp = await client.post("/api/auth/login", json={
        "email": "analyst@test.com",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_analyst_cannot_create_record(client: AsyncClient):
    """Analyst should get 403 when trying to create a record."""
    await client.post("/api/auth/register", json={
        "name": "Analyst",
        "email": "analyst2@test.com",
        "password": "password123",
    })
    from src.database import async_session
    from src.models.user import User
    from sqlalchemy import update
    async with async_session() as session:
        await session.execute(
            update(User).where(User.email == "analyst2@test.com").values(role="analyst")
        )
        await session.commit()

    login_resp = await client.post("/api/auth/login", json={
        "email": "analyst2@test.com",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.post("/api/records", json={
        "amount": 100,
        "type": "income",
        "category": "salary",
        "date": "2026-04-01",
    }, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analyst_cannot_manage_users(client: AsyncClient):
    """Analyst should get 403 when trying to list users."""
    await client.post("/api/auth/register", json={
        "name": "Analyst",
        "email": "analyst3@test.com",
        "password": "password123",
    })
    from src.database import async_session
    from src.models.user import User
    from sqlalchemy import update
    async with async_session() as session:
        await session.execute(
            update(User).where(User.email == "analyst3@test.com").values(role="analyst")
        )
        await session.commit()

    login_resp = await client.post("/api/auth/login", json={
        "email": "analyst3@test.com",
        "password": "password123",
    })
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_full_access(client: AsyncClient):
    """Admin should have access to all endpoints."""
    headers = await make_admin(client)

    # Can create records
    response = await client.post("/api/records", json={
        "amount": 5000,
        "type": "income",
        "category": "salary",
        "date": "2026-04-01",
    }, headers=headers)
    assert response.status_code == 201

    # Can view analytics
    response = await client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200

    # Can manage users
    response = await client.get("/api/users", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_blocked(client: AsyncClient):
    """Unauthenticated requests should get 401."""
    response = await client.get("/api/records")
    assert response.status_code == 401

    response = await client.get("/api/dashboard/summary")
    assert response.status_code == 401

    response = await client.get("/api/users")
    assert response.status_code == 401
