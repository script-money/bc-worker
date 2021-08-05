from loggers import setup_logging_pre
import logging
from dotenv import load_dotenv
from worker import Worker, Operation
import requests as rq
import time
import re

logger = logging.getLogger("get_pk")


def change_proxy_loop(proxies_index: int, proxies: list):
    try:
        logger.info("changing IP...")
        proxies_index += 1
        rq.put(
            "http://127.0.0.1:9090/proxies/🔰国外流量", json={"name": proxies[proxies_index]}
        )
    except IndexError:
        logger.error("not proxy use")
        proxies_index = 0
        rq.put(
            "http://127.0.0.1:9090/proxies/🔰国外流量", json={"name": proxies[proxies_index]}
        )


def batch_operation(
    opt: Operation,
    opt_arg: tuple,
    pk_file: str,
    skip_first: bool = False,
    use_proxy: bool = False,
    change_proxy: bool = False,
    record_path: str = "",
):
    if use_proxy:
        now_proxy = rq.get("http://127.0.0.1:9090/proxies/🔰国外流量").json()["now"]
        proxies = []
        response = rq.get("http://127.0.0.1:9090/proxies/").json()["proxies"]
        for key in response.keys():
            if re.search(r"(IPLC|Trojan)", key) or re.search(r"(IEPL|Trojan)", key):
                proxies.append(key)
    with open(pk_file) as f:
        lines = f.readlines()
        for index, line in enumerate(lines[skip_first:]):
            addr, bip, balance = line.split(",")
            if float(balance) == 0:
                continue
            # 完整闭环操作
            wait_seconds = 60
            if use_proxy:
                proxies_index = proxies.index(now_proxy)
            if int(index) % 20 == 19:
                if change_proxy:
                    change_proxy_loop(proxies_index, proxies)
                else:
                    logger.info(f"wait {wait_seconds} seconds forbid CF ban")
                    time.sleep(wait_seconds)
            result = False
            while not result:
                try:
                    worker = Worker(index, bip, use_proxy)
                    worker.launch()
                    if record_path != "":
                        with open(record_path, "a") as j:
                            j.write(
                                worker.public_key
                                + ","
                                + worker.private_key
                                + ","
                                + str(worker.balance_bitclout)
                                + "\n"
                            )
                    if opt == Operation.BUY:
                        worker.buy(**opt_arg)
                    elif opt == Operation.SEND_CLOUT:
                        if worker.balance_bitclout > 0.01:
                            worker.send_clout(*opt_arg)
                    worker.driver.close()
                    result = True
                    continue
                except Exception as e:
                    logger.warning(f"batch_operation {addr} has error: {e}")
                    if change_proxy:
                        change_proxy_loop(proxies_index, proxies)
                    else:
                        logger.info(f"wait {wait_seconds} seconds then retry")
                        time.sleep(wait_seconds)


if __name__ == "__main__":
    load_dotenv(".env")
    setup_logging_pre()
    batch_operation(
        Operation.SEND_CLOUT,
        # opt_arg=("scriptmoney", 0.05),
        opt_arg=("scriptmoney", "MAX"),
        pk_file="pk/balance_07_31.csv",
        skip_first=True,
        use_proxy=True,
        change_proxy=True,
        record_path="pk/balance_07_31.txt",
    )
