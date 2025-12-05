import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_search_endpoint(client):
    test_data = {"value": 42}
    response = await client.post("/search", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "found" in data
    assert "index" in data
    assert "value" in data
    assert data["value"] == 42

@pytest.mark.asyncio
async def test_array_endpoint(client):
    response = await client.get("/array")
    assert response.status_code == 200
    data = response.json()
    assert "array" in data
    assert "size" in data
    assert len(data["array"]) == data["size"]
    assert data["size"] == 100