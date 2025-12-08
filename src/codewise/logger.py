import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name="codewise"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Formatter
    fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler
    fh = RotatingFileHandler(
        os.path.join(LOG_DIR, "codewise.log"),
        maxBytes=2_000_000,
        backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger
