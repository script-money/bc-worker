import logging
import sys
from logging import Formatter
from logging.handlers import BufferingHandler
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Initialize bufferhandler - will be used for /log endpoints
bufferHandler = BufferingHandler(1000)
bufferHandler.setFormatter(Formatter(LOGFORMAT))
streamHandler = logging.StreamHandler(sys.stderr)
streamHandler.setFormatter(CustomFormatter())
fileHandler = logging.FileHandler(
    "logs/" + datetime.now(timezone.utc).strftime("%m-%d_%H:%M") + ".log"
)


def setup_logging_pre() -> None:
    """
    Early setup for logging.
    Uses INFO loglevel and only the Streamhandler.
    Early messages (before proper logging setup) will therefore only be sent to additional
    logging handlers after the real initialization, because we don't know which
    ones the user desires beforehand.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=LOGFORMAT,
        handlers=[streamHandler, bufferHandler, fileHandler],
    )
