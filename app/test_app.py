"""Basic tests for the status API. Run with: python -m pytest app/"""
from app import app


def test_health():
    client = app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "healthy"}


def test_status():
    client = app.test_client()
    resp = client.get("/status")
    body = resp.get_json()
    assert resp.status_code == 200
    assert body["status"] == "ok"
    assert body["service"] == "shipfast-status-api"
    assert "environment" in body


def test_unknown_route_returns_404():
    client = app.test_client()
    assert client.get("/does-not-exist").status_code == 404
