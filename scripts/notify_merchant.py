import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from roco_tool import fetch_merchant

TOKEN = os.environ["WX_PUSHER_TOKEN"]
UID = os.environ["WX_PUSHER_UID"]


def main():
    result = fetch_merchant()
    if "无法获取" in result or "关闭时段" in result:
        print(f"跳过推送: {result[:50]}")
        return
    resp = requests.post(
        "https://wxpusher.zjiecode.com/api/send/message",
        json={
            "appToken": TOKEN,
            "content": f"🛒 旅行商人商品更新\n\n{result}",
            "contentType": 1,
            "uids": [UID],
        },
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != 1000:
        print(f"推送失败: {data}")


if __name__ == "__main__":
    main()
