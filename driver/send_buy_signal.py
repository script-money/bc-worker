import zmq
import logging
from loggers import setup_logging_pre

logger = logging.getLogger(__name__)

def main():
    setup_logging_pre()
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect('tcp://localhost:5557')
    usd = 0.00011 # 最低0.000100245usd
    username = "scriptmoney"
    signal = '0'+' '+username+' '+str(usd)
    logger.info(f"send: {signal}")
    socket.send_string(signal)

main()

