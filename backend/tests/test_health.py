import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoints(client: AsyncClient) -> None:
    # 1. Test root /health endpoint
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"
    assert "version" in data

    # 2. Test /api/health endpoint
    api_response = await client.get("/api/health")
    assert api_response.status_code == 200
    api_data = api_response.json()
    assert api_data["status"] == "ok"
    assert api_data["db"] == "connected"
