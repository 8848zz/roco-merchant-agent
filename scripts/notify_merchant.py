import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from roco_tool import fetch_merchant


def main():
    result = fetch_merchant()
    if "无法获取" in result or "关闭时段" in result:
        print(f"跳过推送: {result[:50]}")
        return
    for key, val in os.environ.items():
        if not key.startswith("SERVERCHAN_SENDKEY"):
            continue
        tag = key.removeprefix("SERVERCHAN_SENDKEY") or "1"
        resp = requests.post(
            f"https://sctapi.ftqq.com/{val}.send",
            data={
                "title": "🛒 旅行商人商品更新",
                "content": result,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 0:
            print(f"推送成功 [{tag}]")
        else:
            print(f"推送失败 [{tag}]: {data}")


if __name__ == "__main__":
    main()
