def test_health_check_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "service" in data
    assert "uptime_seconds" in data
    assert "timestamp" in data

def test_root_endpoint_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]
    assert "docs_url" in data
