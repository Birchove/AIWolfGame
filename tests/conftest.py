"""Pytest fixtures shared across tests."""

from __future__ import annotations

import pytest

from tests.fixtures.pass_agent import pass_agents


@pytest.fixture(autouse=True)
def stub_api_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    """API integration tests use PassAgent — no real LLM calls."""

    def _build(_cfg, *, repo_root):
        return pass_agents()

    monkeypatch.setattr("aiwerewolf.api.runner.build_agents", _build)
