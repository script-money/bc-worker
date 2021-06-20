from TwitterAPI import TwitterResponse
from time import strptime, struct_time
import re


def convert_timestr_to_timestruct(timestr: str) -> struct_time:
    """
    把twitter的timestr改为timestruct

    Args:
        timestr (str): twitter的timestr格式

    Returns:
        struct_time: Python的结构时间格式
    """
    return strptime(timestr, "%a %b %d %H:%M:%S +0000 %Y")


def filter_newest_tweets(
    old: TwitterResponse, new: TwitterResponse
) -> list[TwitterResponse]:
    """
    两次请求获取新的tweets

    Args:
        old (TwitterResponse): 旧的TwitterResponse
        new (TwitterResponse): 新的TwitterResponse

    Returns:
        list[TwitterResponse]: 新增的TwitterResponse，转为了list
    """
    if old is None:
        return list(new)
    old_ids = list(map(lambda m: m["id"], old))
    new_ids = list(map(lambda m: m["id"], new))
    first = old_ids[0]
    if first in new_ids:
        new_id_list = new_ids[: new_ids.index(first)]
        return [t for t in new if t["id"] in new_id_list]
    return list(new)


def filter_tweets(i: TwitterResponse) -> bool:
    """
    特定条件过滤推特，用于filter函数

    Args:
        i (TwitterResponse): TwitterResponse

    Returns:
        bool: 是否满足条件
    """
    created_at = (
        convert_timestr_to_timestruct(i["user"]["created_at"]).tm_year < 2021
    )  # 2021年前创建
    # 粉丝数是关注数2倍以上
    follow_friends_count = i["user"]["followers_count"] > i["user"]["friends_count"] * 2
    followers_count = i["user"]["followers_count"] > 80000  # 粉丝数大于8万
    verified = i["user"]["verified"]  # 已经过认证
    # return True
    return created_at and follow_friends_count and followers_count and verified


def get_bitclout_username(r: TwitterResponse) -> set[str]:
    """
    获取bitclout用户名集合。检查方式有发私钥和发链接。

    Args:
        r (TwitterResponse): TwitterResponse

    Returns:
        set[str]: 用户名集合
    """
    names = set()
    for index, tweet in enumerate(r):
        urls = tweet["entities"]["urls"]
        text = tweet["text"]
        regex_url = re.compile(r"'expanded_url': 'https:\/\/bitclout.com\/u\/(\w+)")
        regex_pk = re.compile(r"BC\w{53}")
        mo = regex_url.search(str(urls))
        if not mo is None:
            names.add(mo.group(1))
        if regex_pk.match(text):
            names.add(list(r)[index]["user"]["screen_name"])
    return names
