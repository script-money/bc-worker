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
        creator = 'Justin_Sun'
        message = "Greetings investor! @myReclout will open for public coin purchasing in 10 hours. If you want in before the public, please make your purchase during the 5 minutes window opened just for you today April 21st at US Eastern time 12pm, 1pm, 3pm, 5pm and 7pm. @myReclout connects creators & users and rewards you for your engagement."
        signal = f'5 {creator} {message}'
        logger.info(f"send: {signal}")
        socket.send_string(signal)
    except Exception as e:
        logger.error(f"follow fail: {e}")


main()
