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

ROUND_LABELS = ["关闭", "08:00-12:00", "12:00-16:00", "16:00-20:00", "20:00-24:00"]


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


def _check_freshness(initial):
    """返回 True 表示数据是最新的当前轮次，否则 False。"""
    local_round, _ = _current_round()
    if local_round == 0:
        return False
    if initial.get("status") != "open":
        return False
    server_round = initial.get("round")
    if server_round is not None and server_round != local_round:
        return False
    expected_start = f"{_beijing_now().strftime('%Y-%m-%d')} {(local_round - 1) * 4 + 8:02d}:00:00"
    server_started = initial.get("startedAtBeijing")
    if server_started and server_started != expected_start:
        return False
    return True


def _extract_onebiji_item(li):
    name_el = li.select_one(".shop_name")
    price_el = li.select_one(".shop_price")
    limit_el = li.select_one(".gitem em")
    if not name_el or not price_el:
        return None
    return {
        "name": name_el.get_text(strip=True),
        "price": price_el.get_text(strip=True).replace("价格：", ""),
        "limit": limit_el.get_text(strip=True).replace("限购", "") if limit_el else "-",
    }


def _format_item(item):
    name = item.get("name", "未知")
    price = item.get("price", "-")
    limit = item.get("limit", "-")
    category = item.get("category", "")
    desc = item.get("description", "")
    lines = [f"▸ {name}"]
    if category:
        lines.append(f"  分类：{category}")
    lines.append(f"  价格：{price} 洛克贝 | 限购：{limit}")
    if desc:
        lines.append(f"  说明：{desc}")
    return "\n".join(lines)


# ─── 当前轮次解析器（fetch_merchant 使用）───

def _parse_rocokingdom(html):
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="merchant-script-data")
    if not tag:
        return None
    data = json.loads(tag.string)
    initial = data.get("initial", {})
    local_round, period_str = _current_round()

    if local_round == 0:
        return f"当前为关闭时段 ({period_str})，商人未营业。"

    if not _check_freshness(initial):
        return None

    items = initial.get("items", [])
    if not items:
        return "当前轮次暂无商品数据。"
    lines = [f"当前时段：{period_str}（第 {local_round} 轮）"]
    for item in items:
        lines.append("")
        lines.append(_format_item(item))
    return "\n".join(lines)


def _parse_onebiji(html):
    soup = BeautifulSoup(html, "lxml")
    local_round, period_str = _current_round()
    if local_round == 0:
        return f"当前为关闭时段 ({period_str})，商人未营业。"

    items = []
    for li in soup.select("li.li_show"):
        style = li.get("style", "")
        if "display:none" in style:
            continue
        item = _extract_onebiji_item(li)
        if item:
            items.append(item)

    if not items:
        return "当前轮次暂无商品数据。"
    lines = [f"当前时段：{period_str}（第 {local_round} 轮）"]
    for item in items:
        lines.append("")
        lines.append(_format_item(item))
    return "\n".join(lines)


def _parse_ali213(html):
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "未知页面"
    local_round, period_str = _current_round()
    return (
        f"当前时段：{period_str}（第 {local_round} 轮）\n"
        f"来源：{title}\n"
        "数据源为攻略站，未提供结构化商人数据，请参考其他数据源。"
    )


PARSER_MAP = {
    "rocokingdomworld.org": _parse_rocokingdom,
    "onebiji.com": _parse_onebiji,
    "gl.ali213.net": _parse_ali213,
}


# ─── 全轮次解析器（fetch_merchant_all 使用）───

def _parse_rocokingdom_all(html):
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("script", id="merchant-script-data")
    if not tag:
        return None
    data = json.loads(tag.string)
    initial = data.get("initial", {})
    local_round, _ = _current_round()

    if not _check_freshness(initial):
        return None

    rounds_data = initial.get("rounds", {})
    if not rounds_data:
        return _parse_rocokingdom(html)

    lines = [f"当前时段：{ROUND_LABELS[local_round]}（第 {local_round} 轮）\n"]

    for r in range(1, 5):
        items = rounds_data.get(str(r), [])
        lines.append(f"── 第 {r} 轮 ({ROUND_LABELS[r]}) ──")
        if items:
            for item in items:
                lines.append("")
                lines.append(_format_item(item))
        else:
            lines.append("  （无商品数据）")
        lines.append("")
    return "\n".join(lines).strip()


def _parse_onebiji_all(html):
    soup = BeautifulSoup(html, "lxml")
    local_round, _ = _current_round()

    round_items = {1: [], 2: [], 3: [], 4: []}
    for li in soup.select("li.li_show"):
        classes = li.get("class", [])
        item = _extract_onebiji_item(li)
        if not item:
            continue
        for r in range(1, 5):
            if f"show_{r}" in classes:
                round_items[r].append(item)

    lines = [f"当前时段：{ROUND_LABELS[local_round]}（第 {local_round} 轮）\n"]
    for r in range(1, 5):
        items = round_items[r]
        lines.append(f"── 第 {r} 轮 ({ROUND_LABELS[r]}) ──")
        if items:
            for item in items:
                lines.append("")
                lines.append(_format_item(item))
        else:
            lines.append("  （无商品数据）")
        lines.append("")
    return "\n".join(lines).strip()


def _parse_ali213_all(html):
    return _parse_ali213(html)


PARSER_MAP_ALL = {
    "rocokingdomworld.org": _parse_rocokingdom_all,
    "onebiji.com": _parse_onebiji_all,
    "gl.ali213.net": _parse_ali213_all,
}


# ─── 公开 API ───

def _fetch(parser_map):
    for name, url in SOURCES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
        except requests.RequestException:
            continue
        parser = parser_map.get(name)
        if parser:
            result = parser(resp.text)
            if result:
                return result
    return "无法获取商人数据：所有数据源均不可用。"


def fetch_merchant():
    """返回当前轮次商品信息（用于定时推送）。"""
    return _fetch(PARSER_MAP)


def fetch_merchant_all():
    """返回所有轮次完整商品信息（用于手动查询）。"""
    return _fetch(PARSER_MAP_ALL)
