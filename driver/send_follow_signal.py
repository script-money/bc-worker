import zmq
import logging
from loggers import setup_logging_pre

logger = logging.getLogger(__name__)


def main():
    setup_logging_pre()
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:5557")

    try:
        username = "scriptmoney"
        signal = "3" + " " + username
        logger.info(f"send: {signal}")
        socket.send_string(signal)
    except Exception as e:
        logger.error(f"follow fail: {e}")


main()
