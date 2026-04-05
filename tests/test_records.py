"""Tests for financial records CRUD operations."""

import pytest
from httpx import AsyncClient
from tests.conftest import make_admin


@pytest.mark.asyncio
async def test_create_record(client: AsyncClient):
    """Test creating a financial record."""
    headers = await make_admin(client)
    response = await client.post("/api/records", json={
        "amount": 5000.50,
        "type": "income",
        "category": "salary",
        "date": "2026-04-01",
        "description": "April salary",
    }, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 5000.50
    assert data["type"] == "income"
    assert data["category"] == "salary"
    assert data["description"] == "April salary"


@pytest.mark.asyncio
async def test_create_record_validation(client: AsyncClient):
    """Test validation on record creation."""
    headers = await make_admin(client)

    # Negative amount
    response = await client.post("/api/records", json={
        "amount": -100,
        "type": "income",
        "category": "salary",
        "date": "2026-04-01",
    }, headers=headers)
    assert response.status_code == 422

    # Invalid type
    response = await client.post("/api/records", json={
        "amount": 100,
        "type": "invalid",
        "category": "salary",
        "date": "2026-04-01",
    }, headers=headers)
    assert response.status_code == 422

    # Missing required fields
    response = await client.post("/api/records", json={
        "amount": 100,
    }, headers=headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_records_with_pagination(client: AsyncClient):
    """Test listing records with pagination."""
    headers = await make_admin(client)

    # Create multiple records
    for i in range(5):
        await client.post("/api/records", json={
            "amount": 100 + i,
            "type": "income",
            "category": "salary",
            "date": f"2026-04-0{i + 1}",
        }, headers=headers)

    # Get first page
    response = await client.get("/api/records?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total"] == 5
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_filter_records_by_type(client: AsyncClient):
    """Test filtering records by type."""
    headers = await make_admin(client)

    await client.post("/api/records", json={
        "amount": 5000, "type": "income", "category": "salary", "date": "2026-04-01",
    }, headers=headers)
    await client.post("/api/records", json={
        "amount": 1000, "type": "expense", "category": "rent", "date": "2026-04-01",
    }, headers=headers)

    # Filter income only
    response = await client.get("/api/records?type=income", headers=headers)
    data = response.json()
    assert data["total"] == 1
    assert data["data"][0]["type"] == "income"


@pytest.mark.asyncio
async def test_update_record(client: AsyncClient):
    """Test updating a financial record."""
    headers = await make_admin(client)

    # Create
    create_resp = await client.post("/api/records", json={
        "amount": 1000, "type": "expense", "category": "rent", "date": "2026-04-01",
    }, headers=headers)
    record_id = create_resp.json()["id"]

    # Update
    response = await client.put(f"/api/records/{record_id}", json={
        "amount": 1200,
        "description": "Updated rent",
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["amount"] == 1200
    assert response.json()["description"] == "Updated rent"


@pytest.mark.asyncio
async def test_soft_delete_record(client: AsyncClient):
    """Test soft-deleting a record (should not appear in listings)."""
    headers = await make_admin(client)

    # Create
    create_resp = await client.post("/api/records", json={
        "amount": 500, "type": "expense", "category": "dining", "date": "2026-04-01",
    }, headers=headers)
    record_id = create_resp.json()["id"]

    # Delete
    delete_resp = await client.delete(f"/api/records/{record_id}", headers=headers)
    assert delete_resp.status_code == 200

    # Verify it's hidden from list
    list_resp = await client.get("/api/records", headers=headers)
    ids = [r["id"] for r in list_resp.json()["data"]]
    assert record_id not in ids

    # Verify direct access also returns 404
    get_resp = await client.get(f"/api/records/{record_id}", headers=headers)
    assert get_resp.status_code == 404
