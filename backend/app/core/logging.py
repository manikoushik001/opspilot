import logging
import sys
from app.core.config import settings

# Setup standard logger
logger = logging.getLogger(settings.PROJECT_NAME)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{settings.PROJECT_NAME}.{name}")
