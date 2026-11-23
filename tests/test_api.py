def test_dashboard_health_and_assets(tmp_path, monkeypatch):
    monkeypatch.setenv("WATCHTOWER_DB", str(tmp_path / "test.db"))
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    home = client.get("/")
    assert home.status_code == 200
    assert "API Watchtower" in home.text
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/health").json()["status"] == "ok"


def test_add_list_reject_and_delete_target(tmp_path, monkeypatch):
    monkeypatch.setenv("WATCHTOWER_DB", str(tmp_path / "api.db"))
    from app.database import init_db
    from app.main import app
    from fastapi.testclient import TestClient

    init_db()
    client = TestClient(app)

    created = client.post(
        "/api/targets",
        json={"name": "Example API", "url": "https://example.com/health"},
    )
    assert created.status_code == 201
    target_id = created.json()["id"]

    listed = client.get("/api/targets")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Example API"

    duplicate = client.post(
        "/api/targets",
        json={"name": "Duplicate", "url": "https://example.com/health"},
    )
    assert duplicate.status_code == 409

    deleted = client.delete(f"/api/targets/{target_id}")
    assert deleted.status_code == 204
    assert client.get("/api/targets").json() == []
