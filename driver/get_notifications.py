import json
import time
import requests as rq
import os
from request import get_notification
import pandas as pd
import numpy as np
import logging

from loggers import setup_logging_pre

logger = logging.getLogger(__name__)


def generate_reclout_csv(
    pk: str, post_hash: str, number_to_fetch: int = 201, end_index: int = 1
):
    try:
        # get notifications
        notifications_list = []
        profiles_by_public_key = {}
        posts_by_hash = {}
        fetch_start_index = -1
        for i in range(20):
            result = None
            while result is None:
                try:
                    logger.info(f"fetching {fetch_start_index}")
                    notifications, last_index = get_notification(
                        pk,
                        number_to_fetch=number_to_fetch,
                        fetch_start_index=fetch_start_index,
                    )
                    result = True
                except:
                    logger.info("query error, retry")
                    time.sleep(30)
            fetch_start_index = last_index - 1
            notifications_list.extend(notifications["Notifications"])
            profiles_by_public_key.update(notifications["ProfilesByPublicKey"])
            posts_by_hash.update(notifications["PostsByHash"])
            if last_index <= end_index:
                break
            time.sleep(5)
            logger.info("---")

        logger.info("\n")
        logger.info(f"whole notifications_list length: {len(notifications_list)}")
        logger.info(
            f"whole profiles_by_public_key length: {len(profiles_by_public_key)}"
        )
        logger.info(f"whole posts_by_hash length: {len(posts_by_hash)}")
    except Exception as e:
        logger.error("get notifications fail:" + e)

    # generate dataframe
    try:
        data = []
        for k, v in posts_by_hash.items():
            if (
                v["RecloutedPostEntryResponse"] is not None
                and v["RecloutedPostEntryResponse"]["PostHashHex"] == post_hash
            ):
                res = v["ProfileEntryResponse"]
                pk = res["PublicKeyBase58Check"]
                username = res["Username"]
                description = res["Description"]
                coin_price = res["CoinPriceBitCloutNanos"] / 1e9
                post_url = f"https://bitclout.com/posts/{v['PostHashHex']}"
                data.append((post_url, pk, username, description, coin_price))
        if len(data) == 0:
            logger.warning("Reclout data is not found. No csv generate")
            return
        df = pd.DataFrame.from_records(
            data,
            columns=[
                "PostUrl",
                "PublicKey",
                "Username",
                "Description",
                "CoinPriceBitClout",
            ],
        )
        df = df[::-1]
        df.index = np.arange(1, len(df) + 1)
        if not os.path.exists("csv"):
            os.makedirs("csv")
        path = f"./csv/{post_hash}.csv"
        df.to_csv(path)
        logger.info(
            f"reclout list has save to {path}, if is incomplete, try modify number_to_fetch and end_index and retry"
        )
    except Exception as e:
        logger.error("generate csv fail:" + e)


if __name__ == "__main__":
    setup_logging_pre()
    generate_reclout_csv(
        "BC1YLhG4iy3SevnVtxweAftYvQm1xbtrk2XYJBHsLwuc5csAM3wFaCE",
        "54bd3adf130c7579abfadaccc670f3c7f2dbe88ada5212fb85e42f4b9070eae2",
        number_to_fetch=250,
        end_index=1500,
    )
