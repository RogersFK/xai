# ui/logger.py
import logging
import sys

def get_logger(name: str = "XAI") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:         
        return logger

    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    sys.stdout.reconfigure(line_buffering=True)
    return logger