"""Production entry — LLM werewolf game."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from aiwerewolf.agents.factory import build_agents  # noqa: E402
from aiwerewolf.engine.loop import GameLoop  # noqa: E402
from aiwerewolf.logging.recorder import Recorder  # noqa: E402
from schema.config import load_app_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Werewolf — LLM game")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=_ROOT / "Config",
        help="Directory containing default.yaml and secrets.yaml",
    )
    parser.add_argument("--count", type=int, default=1, help="Number of games to run")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed base")
    parser.add_argument(
        "--record",
        type=Path,
        default=None,
        help="Write JSONL event log (default: logs/game-{seed}.jsonl when --count 1)",
    )
    args = parser.parse_args()

    cfg = load_app_config(args.config_dir, use_secrets=True)
    logger.info(
        "Loaded config: llm=%s/%s base_url=%s",
        cfg.llm.provider,
        cfg.llm.model,
        cfg.llm.base_url or "(default)",
    )

    if not cfg.llm_ready():
        logger.error("LLM api_key missing — edit Config/secrets.yaml")
        return 1

    for i in range(args.count):
        seed = args.seed + i
        agents = build_agents(cfg, repo_root=_ROOT)
        recorder = None
        record_path = args.record
        if record_path is None and args.count == 1:
            log_dir = _ROOT / cfg.logging.output_dir
            log_dir.mkdir(parents=True, exist_ok=True)
            record_path = log_dir / f"game-{seed}.jsonl"
        if record_path is not None:
            path = record_path
            if args.count > 1:
                path = path.with_stem(f"{path.stem}-{i}")
            recorder = Recorder(output_path=path)
            logger.info("Recording events to %s", path)
        loop = GameLoop(
            agents,
            max_rounds=cfg.game.max_rounds,
            recorder=recorder,
            cfg=cfg,
        )
        result = loop.run(seed=seed)
        logger.info(
            "Game %d: winner=%s rounds=%d reason=%s",
            i + 1,
            result.winner,
            result.round_count,
            result.win_reason,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
