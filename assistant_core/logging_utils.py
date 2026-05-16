from __future__ import annotations

from pathlib import Path

from loguru import logger


def configure_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level="INFO")
    logger.add(log_dir / "local_ai_orchestrator.log", rotation="10 MB", retention="14 days", level="DEBUG")
