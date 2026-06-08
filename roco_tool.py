import json
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SOURCES = [
    ("rocokingdomworld.org", "https://rocokingdomworld.org/zh/merchant/"),
    ("onebiji.com", "https://www.onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1"),
    ("gl.ali213.net", "https://gl.ali213.net/z/153119/"),
]


def _beijing_now():
    return datetime.now(timezone(timedelta(hours=8)))


def _current_round():
    h = _beijing_now().hour
    if 8 <= h < 12:
        return 1, "08:00-12:00"
    if 12 <= h < 16:
        return 2, "12:00-16:00"
    if 16 <= h < 20:
        return 3, "16:00-20:00"
    if 20 <= h < 24:
        return 4, "20:00-24:00"
    return 0, "关闭时段 (00:00-08:00)"


def _parse_rocokingdom(html):
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="merchant-script-data")
    if not tag:
        return None
    data = json.loads(tag.string)
    initial = data.get("initial", {})
    status = initial.get("status", "")
    round_num, period_str = _current_round()
    if status == "closed":
        return f"当前为关闭时段 ({period_str})，商人未营业。"

    items = initial.get("items", [])
    if not items:
        return "当前轮次暂无商品数据。"
    lines = [f"当前时段：{period_str}（第 {round_num} 轮）"]
    for item in items:
        name = item.get("name", "未知")
        price = item.get("price", "-")
        limit = item.get("limit", "-")
        category = item.get("category", "")
        desc = item.get("description", "")
        lines.append(f"\n▸ {name}")
        lines.append(f"  分类：{category}")
        lines.append(f"  价格：{price} 洛克贝 | 限购：{limit}")
        if desc:
            lines.append(f"  说明：{desc}")
    return "\n".join(lines)


def _parse_onebiji(html):
    soup = BeautifulSoup(html, "lxml")
    round_num, period_str = _current_round()
    if round_num == 0:
        return f"当前为关闭时段 ({period_str})，商人未营业。"

    items = []
    for li in soup.select("li.li_show"):
        name_el = li.select_one(".shop_name")
        price_el = li.select_one(".shop_price")
        limit_el = li.select_one(".gitem em")
        if not name_el or not price_el:
            continue
        name = name_el.get_text(strip=True)
        price_text = price_el.get_text(strip=True).replace("价格：", "")
        limit = limit_el.get_text(strip=True).replace("限购", "") if limit_el else "-"
        items.append({"name": name, "price": price_text, "limit": limit})

    if not items:
        return "当前时段暂无商品数据。"
    lines = [f"当前时段：{period_str}（第 {round_num} 轮）"]
    for item in items:
        lines.append(f"\n▸ {item['name']}")
        lines.append(f"  价格：{item['price']} 洛克贝 | 限购：{item['limit']}")
    return "\n".join(lines)


def _parse_ali213(html):
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "未知页面"
    round_num, period_str = _current_round()
    lines = [
        f"当前时段：{period_str}（第 {round_num} 轮）",
        f"来源：{title}",
        "数据源为攻略站，未提供结构化商人数据，请参考其他数据源。"
    ]
    return "\n".join(lines)


PARSER_MAP = {
    "rocokingdomworld.org": _parse_rocokingdom,
    "onebiji.com": _parse_onebiji,
    "gl.ali213.net": _parse_ali213,
}


def fetch_merchant():
    for name, url in SOURCES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
        except requests.RequestException:
            continue

        parser = PARSER_MAP.get(name)
        if parser:
            result = parser(resp.text)
            if result:
                return result
    return "无法获取商人数据：所有数据源均不可用。"
