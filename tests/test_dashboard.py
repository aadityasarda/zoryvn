"""Tests for dashboard analytics endpoints."""

import pytest
from httpx import AsyncClient
from tests.conftest import make_admin


@pytest.mark.asyncio
async def test_dashboard_summary(client: AsyncClient):
    """Test financial summary endpoint."""
    headers = await make_admin(client)

    # Create test records
    await client.post("/api/records", json={
        "amount": 5000, "type": "income", "category": "salary", "date": "2026-04-01",
    }, headers=headers)
    await client.post("/api/records", json={
        "amount": 3000, "type": "income", "category": "freelance", "date": "2026-04-02",
    }, headers=headers)
    await client.post("/api/records", json={
        "amount": 1500, "type": "expense", "category": "rent", "date": "2026-04-01",
    }, headers=headers)

    response = await client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 8000.0
    assert data["total_expenses"] == 1500.0
    assert data["net_balance"] == 6500.0
    assert data["record_count"] == 3


@pytest.mark.asyncio
async def test_dashboard_category_totals(client: AsyncClient):
    """Test category-wise totals endpoint."""
    headers = await make_admin(client)

    await client.post("/api/records", json={
        "amount": 5000, "type": "income", "category": "salary", "date": "2026-04-01",
    }, headers=headers)
    await client.post("/api/records", json={
        "amount": 2000, "type": "income", "category": "salary", "date": "2026-04-02",
    }, headers=headers)
    await client.post("/api/records", json={
        "amount": 1000, "type": "expense", "category": "rent", "date": "2026-04-01",
    }, headers=headers)

    response = await client.get("/api/dashboard/category-totals", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 2  # At least salary and rent

    # Find salary category
    salary = next(d for d in data if d["category"] == "salary")
    assert salary["total"] == 7000.0
    assert salary["count"] == 2


@pytest.mark.asyncio
async def test_dashboard_trends(client: AsyncClient):
    """Test trends endpoint."""
    headers = await make_admin(client)

    await client.post("/api/records", json={
        "amount": 5000, "type": "income", "category": "salary", "date": "2026-04-01",
    }, headers=headers)

    response = await client.get("/api/dashboard/trends?interval=monthly", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["interval"] == "monthly"
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_dashboard_recent(client: AsyncClient):
    """Test recent transactions endpoint."""
    headers = await make_admin(client)

    for i in range(3):
        await client.post("/api/records", json={
            "amount": 100 * (i + 1),
            "type": "income",
            "category": "salary",
            "date": f"2026-04-0{i + 1}",
        }, headers=headers)

    response = await client.get("/api/dashboard/recent?limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 2


@pytest.mark.asyncio
async def test_dashboard_empty(client: AsyncClient):
    """Test dashboard with no records."""
    headers = await make_admin(client)

    response = await client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 0
    assert data["total_expenses"] == 0
    assert data["net_balance"] == 0
    assert data["record_count"] == 0
