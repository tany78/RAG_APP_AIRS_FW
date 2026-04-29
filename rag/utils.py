import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name, file):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.FileHandler(LOG_DIR / file, mode='a', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
    return logger

def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
