"""Role-scoped game guide extraction."""

from pathlib import Path

from schema.enums import Role

from aiwerewolf.prompts.game_guide_sections import build_role_scoped_game_guide


def test_wolf_guide_includes_camp_not_full_file() -> None:
    repo = Path(__file__).resolve().parents[2]
    full = (repo / "game_guide.md").read_text(encoding="utf-8")
    scoped = build_role_scoped_game_guide(
        repo_root=repo, guide_file="game_guide.md", role=Role.WOLF
    )
    assert len(scoped) < len(full) * 0.85
    assert "悍跳" in scoped
    assert "术语速查" in scoped or "金水" in scoped


def test_villager_guide_has_opponent_intel() -> None:
    repo = Path(__file__).resolve().parents[2]
    scoped = build_role_scoped_game_guide(
        repo_root=repo, guide_file="game_guide.md", role=Role.VILLAGER
    )
    assert "普通村民" in scoped or "村民" in scoped
    assert "狼" in scoped


def test_seer_guide_excludes_full_wolf_camp_detail() -> None:
    repo = Path(__file__).resolve().parents[2]
    wolf = build_role_scoped_game_guide(
        repo_root=repo, guide_file="game_guide.md", role=Role.WOLF
    )
    seer = build_role_scoped_game_guide(
        repo_root=repo, guide_file="game_guide.md", role=Role.SEER
    )
    assert len(seer) < len(wolf)
