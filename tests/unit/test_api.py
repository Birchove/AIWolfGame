"""FastAPI tests."""

import time

import pytest
from fastapi.testclient import TestClient

from aiwerewolf.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    app = create_app(config_dir=root / "Config", repo_root=root)
    return TestClient(app)


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "llm_ready" in data


def test_create_and_get_game(client: TestClient) -> None:
    resp = client.post("/games", json={"seed": 1})
    assert resp.status_code == 200
    game_id = resp.json()["game_id"]

    status = None
    for _ in range(100):
        status = client.get(f"/games/{game_id}").json()
        if status["status"] == "complete":
            break
        time.sleep(0.05)

    assert status is not None
    assert status["status"] == "complete"
    events = client.get(f"/games/{game_id}/events").json()
    assert isinstance(events, list)
    assert any(e["type"] == "game_over" for e in events)
