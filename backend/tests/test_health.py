from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_reports_the_deployed_commit(monkeypatch):
    monkeypatch.delenv("SECOND_LOOK_COMMIT", raising=False)
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    assert client.get("/version").json() == {"commit": "unknown"}

    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    assert client.get("/version").json() == {"commit": "abc123"}

    monkeypatch.setenv("SECOND_LOOK_COMMIT", "def456")
    assert client.get("/version").json() == {"commit": "def456"}
