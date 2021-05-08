import sys
from worker import Worker
from loggers import setup_logging_pre
import logging
from dotenv import load_dotenv
import time
import random
import requests as rq
import re


logger = logging.getLogger('get_pk')

def change_proxy_loop(proxies_index: int, proxies:list):
    try:
        logger.info('changing IP...')
        proxies_index += 1
        rq.put("http://127.0.0.1:9090/proxies/🔰国外流量",
               json={"name": proxies[proxies_index]})
    except IndexError:
        logger.error("not proxy use")
        proxies_index = 0
        rq.put("http://127.0.0.1:9090/proxies/🔰国外流量",
               json={"name": proxies[proxies_index]})
        
def main(file, use_proxy=True, change_proxy=False):
    try:
        if use_proxy:
            now_proxy = rq.get("http://127.0.0.1:9090/proxies/🔰国外流量").json()['now']
            proxies = []
            response = rq.get("http://127.0.0.1:9090/proxies/").json()['proxies']
            for key in response.keys():
                if re.search(r"(IPLC|Trojan)", key):
                    proxies.append(key)

        with open(file, 'r') as f:
            lines = f.readlines()
            wait_seconds = 60
            if use_proxy:
                proxies_index = proxies.index(now_proxy)
            for index, line in enumerate(lines):
                if index % 20 == 19:
                    if change_proxy:
                        change_proxy_loop(proxies_index, proxies)
                    else:
                        logger.info(f"wait {wait_seconds} seconds forbid CF ban")
                        time.sleep(wait_seconds)
                bip39 = line.strip()
                result = None
                while not result:
                    try:
                        worker = Worker(str(index), bip39)
                        worker.launch()
                        with open('pk/done_info.txt', 'a') as j:
                            j.write(worker.public_key+','+bip39 +
                                    ','+str(worker.balance_usd)+'\n')
                        worker.driver.close()
                        result = True
                    except:
                        if change_proxy:
                            change_proxy_loop(proxies_index, proxies)
                        else:
                            logger.info(f"wait {wait_seconds} seconds then retry")
                            time.sleep(wait_seconds)
    except Exception as exp:
        logger.exception(f"Fatal exception:{exp}")

if __name__ == "__main__":
    load_dotenv('.env')
    setup_logging_pre()
    main(file='pk/test_3_accounts.txt', use_proxy=False, change_proxy=False)
