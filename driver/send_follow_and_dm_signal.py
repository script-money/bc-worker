import zmq
import logging
from loggers import setup_logging_pre

logger = logging.getLogger(__name__)

def main():
    setup_logging_pre()
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect('tcp://localhost:5557')

    try:
        username = 'ShabbyPhilosoph'
        content = 'Hello world'
        signal = '7'+' '+username+' '+content
        logger.info(f"send: {signal}")
        socket.send_string(signal)
    except Exception as e:
        logger.error(f"follow_and_dm fail: {e}")


main()
