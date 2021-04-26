import requests as rq
import logging
import os
from dotenv import load_dotenv
from loggers import setup_logging_pre

logger = logging.getLogger(__name__)

URL = "https://api.bitclout.com/"

HEADERS = {
    'Content-Type': 'application/json'
}

PROXIES = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

load_dotenv('.env')
proxy_server = os.getenv('PROXY_URL')

def get_hodlers_for_public_key(username: str, number_to_fetch:int=100):
    data_dict = {
        "PublicKeyBase58Check": "", 
        "Username": username,
        "LastPublicKeyBase58Check": "",
        "NumToFetch": number_to_fetch,
        "FetchHodlings": False, 
        "FetchAll": False
    }
    try:
        proxies = {}    
        if proxy_server != "" and proxy_server != None:
            proxies = PROXIES
        wait_seconds = number_to_fetch/10
        logger.info(f"querying data, wait {wait_seconds} seconds")
        res_json = rq.post(URL + "get-hodlers-for-public-key", json=data_dict,
                           headers=HEADERS, proxies=proxies, timeout=wait_seconds).json()
        return res_json
    except rq.exceptions.Timeout:
        logger.warning('timeout, please checkout network')
    except Exception as e:
        logger.warning(f"get holders for public key fail, error: {e}")
        return {}

def find_investors(res_json: dict) -> dict[str, float]:
    holders = res_json['Hodlers']
    return {holder['ProfileEntryResponse']['Username']: round(
        holder['BalanceNanos']/1E9, 4) for holder in holders if holder['ProfileEntryResponse'] is not None} 

def get_notification(public_key: str, number_to_fetch: int = 50) -> dict:
    data_dict = {
        "PublicKeyBase58Check": public_key,
        "FetchStartIndex": -1, 
        "NumToFetch": number_to_fetch
    }
    try:
        proxies = {}
        if proxy_server != "" and proxy_server != None:
            proxies = PROXIES
        wait_seconds = number_to_fetch/10
        logger.info(f"querying data, wait {wait_seconds} seconds")
        res_json = rq.post(URL + "get-notifications",json=data_dict, 
                           headers=HEADERS, proxies=proxies, timeout=wait_seconds).json()
        return res_json
    except rq.exceptions.Timeout:
        logger.warning('timeout, please checkout network')
    except Exception as e:
        logger.warning(f"get notification fail, error: {e}")
        return {}


def find_reclout_list(res_json:dict, post_hash:str) -> str:
    if not res_json or post_hash=="":
        logger.error("please fill query parameter in find_reclout_list")
        return
    notifications = res_json['Notifications']
    profiles_by_pk = res_json['ProfilesByPublicKey']
    posts_by_hash = res_json['PostsByHash']
    reclout_users = [
        profiles_by_pk[v['PosterPublicKeyBase58Check']]['Username'] 
        for k, v in posts_by_hash.items() 
        if v['RecloutedPostEntryResponse'] is not None 
            and v['RecloutedPostEntryResponse']['PostHashHex'] == post_hash
    ]
    return '/'.join(reclout_users)

if __name__ == "__main__":
    setup_logging_pre()
    # users = find_reclout_list(
    #     get_notification(
    #         "BC1YLhG4iy3SevnVtxweAftYvQm1xbtrk2XYJBHsLwuc5csAM3wFaCE", number_to_fetch=300),
    #     "54bd3adf130c7579abfadaccc670f3c7f2dbe88ada5212fb85e42f4b9070eae2"
    # )
    users = find_investors(get_hodlers_for_public_key('Lu1s'))

    print(users)
