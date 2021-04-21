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

def change_proxy(proxy_name:str):
    res = rq.put("http://127.0.0.1:9090/proxies/🔰国外流量",json={"name": proxy_name})
    return res.status_code

def main(file):
    return_code = 1
    try:
        now_proxy = rq.get("http://127.0.0.1:9090/proxies/🔰国外流量").json()['now']
        proxies = []
        response = rq.get("http://127.0.0.1:9090/proxies/").json()['proxies']
        for key in response.keys():
            if re.search(r"(IPLC|Trojan)", key):
                proxies.append(key)

        with open(file, 'r') as f:
            lines = f.readlines()
            proxies_index = proxies.index(now_proxy)
            for index, line in enumerate(lines):
                if index % 15 == 14:
                    try:
                        logger.info('changing IP...')
                        proxies_index += 1
                        change_proxy(proxies[proxies_index])        
                    except IndexError:
                        logger.error("not proxy use")
                        proxies_index = 0
                        change_proxy(proxies[proxies_index])
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
                        logger.warn(f"error when process {bip39}, change ip and retry")
                        proxies_index += 1
                        change_proxy(proxies[proxies_index])   
    except KeyboardInterrupt:
        logger.info('SIGINT received, aborting ...')
        return_code = 0
    except SystemExit as e:
        return_code = e
    except Exception as exp:
        logger.exception(f"Fatal exception:{exp}")
    finally:
        sys.exit(return_code)

if __name__ == "__main__":
    load_dotenv('.env')
    setup_logging_pre()
    main(file='pk/part.txt')
