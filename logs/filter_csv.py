import re
import pandas as pd
from datetime import datetime, timezone

# TODO 有部分账户的余额可能没转出，全部跑一遍后对失败的数据再进行查询


def main(csv_path: str, log_path: str):
    success_address = []
    with open(log_path) as log_file:
        lines = log_file.readlines()
        for index, line in enumerate(lines):
            if "to scriptmoney success" in line:
                mo = re.search(r"BC\w{53}", line)
                success_address.append(mo.group())

    df = pd.read_csv(csv_path)
    unsuccess_df = df[~df["address"].isin(success_address)]
    export_df = unsuccess_df.reset_index()
    export_df[["address", "bip39", "clout"]].to_csv(
        f'pk/{datetime.now(timezone.utc).strftime("%m-%d_%H:%M")}.csv'
    )


if __name__ == "__main__":
    main("./pk/06-24_14:13.csv", "./logs/06-24_14:13.log")
