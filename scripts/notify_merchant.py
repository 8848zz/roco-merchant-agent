import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from roco_tool import fetch_merchant

SENDKEY = os.environ["SERVERCHAN_SENDKEY"]


def main():
    result = fetch_merchant()
    if "无法获取" in result or "关闭时段" in result:
        print(f"跳过推送: {result[:50]}")
        return
    resp = requests.post(
        f"https://sctapi.ftqq.com/{SENDKEY}.send",
        data={
            "title": "🛒 旅行商人商品更新",
            "content": result,
        },
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != 0:
        print(f"推送失败: {data}")


if __name__ == "__main__":
    main()
