import zmq
import logging
import asyncio
from .loggers import setup_logging_pre

logger = logging.getLogger(__name__)

async def main():
    setup_logging_pre()
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://*:5555')
    bitclout = 0.0001
    username = "scriptmoney"
    signal = '0'+' '+username+' '+str(bitclout)
    logger.info(f"send: {signal}")
    socket.send_string(signal)

asyncio.run(main())

