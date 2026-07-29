import logging
from logging.handlers import RotatingFileHandler

from .paths import get_log_dir


def get_logger() -> logging.Logger:
    logger = logging.getLogger("pdf_image_toolkit")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_file = get_log_dir() / "app.log"

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger