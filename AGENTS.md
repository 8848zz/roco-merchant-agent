# 洛可可王国旅行商人 — ReAct 智能体

## 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 lxml
export DEEPSEEK_API_KEY="sk-..."
python main.py
```

- 无测试框架/类型检查/lint，只能 `python main.py` 手动测试

## 架构

```
main.py → react_loop.py (run_react_agent) → llm_client.py → DeepSeek API
                                          → roco_tool.py → 网页爬取
```

| 文件 | 职责 | 入口 |
|------|------|------|
| `main.py` | CLI 输入循环，定义 LLM 可见的 `fetch_merchant` 包装器 | `python main.py` |
| `react_loop.py` | ReAct 引擎，system prompt 动态注入当前北京时间 `{now}` | `run_react_agent(query, tools)` |
| `llm_client.py` | `chat(messages) → str`，封装 `api.deepseek.com/v1/chat/completions` | |
| `roco_tool.py` | `fetch_merchant()`（当前轮次）+ `fetch_merchant_all()`（全部轮次） | |
| `config.py` | `LLM_MODEL=deepseek-chat`, `API_BASE_URL`, `MAX_STEPS=5` | |
| `memory.py` | 对话日志（`add_message`, `print_history`），**不传给 LLM**，Agent 每轮失忆 | |
| `scripts/notify_merchant.py` | 定时推送脚本，调用 `fetch_merchant()` 只拿当前轮次 | GitHub Actions |

## 关键约束

- **LLM 只暴露一个工具：** `fetch_merchant`（`main.py` 定义为 `fetch_merchant_all` 的包装器）。LLM 不区分单轮/全轮，由它自己从数据中推断时段映射。
- **反幻觉规则（system prompt）：** "关于商人和商品的问题，请先调用工具获取数据后据实回答。关于时间、日期、一般知识等独立问题，可以直接回答。所有商品价格和数量必须严格基于工具返回的数据，不得编造。"
- **system prompt 的 `{now}` 占位符** 在 `run_react_agent` 中替换为当前北京时间（`replace` 而非 `format`，避免与 JSON 花括号冲突）。
- **LLM 输出格式：** JSONL，每行一个 `{"type": "thought"|"tool_call"|"final_answer", ...}`。`tool_call` 必须只调 `fetch_merchant`。
- **数据时效性（staleness 检测）：** 主数据源 `rocokingdomworld` 校验 `status=open`、`round` 匹配当前时段、`startedAtBeijing` 匹配预期；否则跳过备用源。

## 数据源

| 优先级 | URL | 解析方式 |
|--------|-----|----------|
| 1 | `rocokingdomworld.org/zh/merchant/` | 内嵌 `<script id="merchant-script-data">` JSON，**最可靠** |
| 2 | `onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1` | HTML，CSS 类 `show_N`/`display:none` 划分轮次（首页是菜谱博客，工具在此子路径） |
| 3 | `gl.ali213.net/z/153119/` | 攻略站，无结构化数据，仅兜底 |
| 兜底 | — | 返回 `"无法获取商人数据"` |

- **时段（北京时间）：** 08:00-12:00 / 12:00-16:00 / 16:00-20:00 / 20:00-24:00（关闭时段 00:00-08:00）
- **网站结构变更** 可能导致解析失败，需维护 `roco_tool.py`

## 定时推送（cron-job.org → GitHub Actions → Server酱 → 微信）

- **调度源：** [cron-job.org](https://cron-job.org) 每天 8 次调用 GitHub API 触发 `workflow_dispatch`（08:05/09:05/12:05/13:05/16:05/17:05/20:05/21:05 北京时间）
- **GitHub Actions**（`.github/workflows/merchant.yml`）仅保留 `workflow_dispatch`，不设 cron
- **Secrets（GitHub）：** `SERVERCHAN_SENDKEY[_N]`（Server酱，多账号加 `_2`、`_3` 后缀）+ `GH_PAT`（GitHub PAT，需 `workflow` 权限）
- **推送脚本：** `scripts/notify_merchant.py`，调用 `roco_tool.fetch_merchant()` 并推送至所有 `SERVERCHAN_SENDKEY*` 渠道
- **爬虫依赖：** `requests`, `beautifulsoup4`, `lxml`

## 测试验证

优化后通过以下 6 个问题模拟完整对话验证行为：
```python
from react_loop import run_react_agent
from roco_tool import fetch_merchant_all as _fetch_all
def fetch_merchant():
    return _fetch_all()
for q in ["今天卖什么", "现在 是几点", "你好",
          "你现在能查到多少远行商人信息",
          "有昨天的售卖情况吗", "世界最高峰是什么"]:
    print(f"Q: {q}\\nA: {run_react_agent(q, tools=[fetch_merchant])}\\n")
```

预期结果：
- 商品问题 → 调工具，基于数据回答
- 时间问题 → 直接答（prompt 注入的北京时间）
- 闲聊/知识 → 直接答，不调工具
- 历史数据 → 如实说没有，不编造

## DeepSeek API

- `https://api.deepseek.com/v1/chat/completions`，模型 `deepseek-chat`，中国大陆可直连（无需 VPN）
- `DEEPSEEK_API_KEY` 环境变量，建议写入 `~/.bashrc`/`~/.zshrc`
