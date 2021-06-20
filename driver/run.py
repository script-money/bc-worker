import zmq
import sys
import logging
from worker import Worker
import threading
import queue
import os
from dotenv import load_dotenv
from loggers import setup_logging_pre
from pid.decorator import pidfile
from pid.base import PidFileAlreadyLockedError

logger = logging.getLogger("selenium_runner")


def check_account():
    private_key = os.getenv("PRIVATE_KEY")
    if private_key is None:
        return None
    return private_key


def worker(_thread_index, _private_key, _queue):
    sub_worker = Worker(_thread_index, _private_key)
    sub_worker.launch()
    while True:
        if not sub_worker.is_busy and not _queue.empty():
            signal = _queue.get()
            logger.info(f"signal:{signal}")
            op = str(signal, "utf_8")
            parameters = op.split(" ")
            sub_worker.dispatcher(parameters[0], parameters[1:])


@pidfile()
def main():
    return_code = 1
    try:
        load_dotenv(".env")
        max_thread = 1  # 开几个selenium
        queue_size = 100
        logger.info(
            f"selenium worker number is {max_thread}, task queue size is {queue_size}"
        )
        queue_instance = queue.Queue(queue_size)

        context = zmq.Context()
        receiver = context.socket(zmq.PULL)
        receiver.bind("tcp://*:5557")

        private_key = check_account()
        if private_key is None:
            logger.error("please set private key in .env")
            raise SystemExit

        for t in range(max_thread):
            threading.Thread(
                target=worker, args=(t, private_key, queue_instance), daemon=True
            ).start()

        while True:
            msg = receiver.recv()
            logger.info(f"recieve message: {msg}")
            try:
                queue_instance.put(msg, block=False)
            except queue.Full:
                logger.warning("Task queue is full")
    except KeyboardInterrupt:
        logger.info("SIGINT received, aborting ...")
        return_code = 0
    except SystemExit as e:
        return_code = e
    except Exception as exp:
        logger.exception(f"Fatal exception:{exp}")
    finally:
        sys.exit(return_code)


try:
    setup_logging_pre()
    main()
except PidFileAlreadyLockedError:
    logger.error("run.py is running already")
