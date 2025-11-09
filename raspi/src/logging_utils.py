from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from .config_loader import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    logger.remove()
    logger.add(sys.stdout, level=config.level, colorize=True, enqueue=True)
    log_path = Path(config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        level=config.level,
        enqueue=True,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

