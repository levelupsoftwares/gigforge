from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# test Health API

def test_health():
    response  = client.get("/api/v1/health")

    assert response.status_code == 200

    assert response.json() == {"message":"healthy"}
