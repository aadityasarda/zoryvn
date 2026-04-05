import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["role"] == "viewer"  # Default role
    assert data["status"] == "active"
    assert "password" not in data  # Password hash must never be exposed


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with an already-used email."""
    payload = {"name": "User", "email": "dup@example.com", "password": "password123"}
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["error"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Test registration with invalid email format."""
    response = await client.post("/api/auth/register", json={
        "name": "User",
        "email": "not-an-email",
        "password": "password123",
    })
    assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Test registration with password too short."""
    response = await client.post("/api/auth/register", json={
        "name": "User",
        "email": "user@test.com",
        "password": "123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login returns JWT token."""
    # Register first
    await client.post("/api/auth/register", json={
        "name": "User",
        "email": "login@test.com",
        "password": "password123",
    })
    # Login
    response = await client.post("/api/auth/login", json={
        "email": "login@test.com",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with incorrect password."""
    await client.post("/api/auth/register", json={
        "name": "User",
        "email": "wrong@test.com",
        "password": "password123",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrong@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent email."""
    response = await client.post("/api/auth/login", json={
        "email": "nobody@test.com",
        "password": "password123",
    })
    assert response.status_code == 401
