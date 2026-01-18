import logging
import sys


def get_logger(name: str = __name__, silence: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)

    if silence:
        logger.setLevel(logging.CRITICAL + 1)
        logger.handlers.clear()
        logger.propagate = False
        return logger

    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger
