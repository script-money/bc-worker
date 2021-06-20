import zmq
import logging
from loggers import setup_logging_pre
from dotenv import load_dotenv
import sys
import os
from TwitterAPI import TwitterAPI, TwitterResponse, TwitterConnectionError
from utils import filter_newest_tweets, filter_tweets, get_bitclout_username
import time
import random

logger = logging.getLogger(__name__)

load_dotenv(".env")
consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token_key = os.getenv("ACCESS_TOKEN_KEY")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")
proxy_url = os.getenv("PROXY_URL")


def main():
    setup_logging_pre()
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.connect("tcp://localhost:5557")
    api = TwitterAPI(
        consumer_key,
        consumer_secret,
        access_token_key,
        access_token_secret,
        proxy_url=proxy_url,
    )
    last_timestamp = 0
    last_response = None
    cooldown = 60
    while True:
        try:
            new_response: TwitterResponse = api.request(
                "search/tweets", {"q": "bitclout"}
            )
            twitter_check_list = filter_newest_tweets(last_response, new_response)
            last_response = new_response
            if len(twitter_check_list) != 0:
                usernames = get_bitclout_username(
                    filter(filter_tweets, twitter_check_list)
                )  # filter
                # TODO use cache to resolve duplicate username
                if len(usernames) != 0:
                    for username in usernames:
                        interval = time.time() - last_timestamp
                        if interval > cooldown:
                            usd = 0.1  # min 0.000100245usd
                            signal = "0" + " " + username + " " + str(usd)
                            logger.info(f"send: {signal}")
                            socket.send_string(signal)
                            last_timestamp = time.time()
                            logger.info(f"newest request timestamp is {last_timestamp}")
                        else:
                            wait_seconds = cooldown - interval
                            logger.info(f"sleep {wait_seconds} seconds...")
                            time.sleep(wait_seconds)
                            continue
                else:
                    logger.info("no filter usernames")
            else:
                logger.info("no new tweets")
        except TwitterConnectionError:
            time.sleep(5)
        except Exception as e:
            logger.error(f"buy fail: {e}")
        finally:
            time.sleep(random.uniform(5, 7))


main()
