"""WebSocket view filtering tests."""

import json
import time

import pytest
from fastapi.testclient import TestClient

from aiwerewolf.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    return TestClient(create_app(config_dir=root / "Config", repo_root=root))


def test_ws_public_view_filters_private_and_god(client: TestClient) -> None:
    resp = client.post("/games", json={"seed": 2})
    game_id = resp.json()["game_id"]

    for _ in range(100):
        status = client.get(f"/games/{game_id}").json()
        if status["status"] == "complete":
            break
        time.sleep(0.05)

    with client.websocket_connect(f"/ws/games/{game_id}?view=public") as ws:
        events = []
        while len(events) < 500:
            data = ws.receive_json()
            events.append(data)
            if data.get("type") == "game_over":
                break

    assert events
    for e in events:
        assert e["visibility"] == "public"
        assert not str(e["visibility"]).startswith("private")
    types = {e["type"] for e in events}
    assert "game_start" not in types


def test_ws_god_view_includes_game_start(client: TestClient) -> None:
    resp = client.post("/games", json={"seed": 3})
    game_id = resp.json()["game_id"]

    for _ in range(100):
        status = client.get(f"/games/{game_id}").json()
        if status["status"] == "complete":
            break
        time.sleep(0.05)

    with client.websocket_connect(f"/ws/games/{game_id}?view=god") as ws:
        events = []
        while len(events) < 500:
            data = ws.receive_json()
            events.append(data)
            if data.get("type") == "game_over":
                break

    starts = [e for e in events if e["type"] == "game_start"]
    assert starts
    assert "roles" in starts[0]["payload"]
