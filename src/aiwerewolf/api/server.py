"""Run spectator server: API + built frontend UI."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import uvicorn

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from schema.config import load_app_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _check_setup() -> None:
    cfg = load_app_config(_ROOT / "Config", use_secrets=True)
    secrets = _ROOT / "Config" / "secrets.yaml"
    dist = _ROOT / "frontend" / "dist"

    if not secrets.is_file():
        logger.warning(
            "Config/secrets.yaml missing — copy from Config/secrets.yaml.example "
            "and set llm.api_key"
        )
    elif not cfg.llm_ready():
        logger.warning("llm.api_key is empty in Config/secrets.yaml")
    else:
        logger.info(
            "LLM ready: provider=%s model=%s",
            cfg.llm.provider,
            cfg.llm.model,
        )

    if not dist.is_dir():
        logger.warning(
            "Build frontend first: cd frontend && npm install && npm run build"
        )
    else:
        logger.info("Spectator UI: http://127.0.0.1:8000/")


if __name__ == "__main__":
    _check_setup()
    uvicorn.run(
        "aiwerewolf.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
