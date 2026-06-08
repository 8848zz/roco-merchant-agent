# 洛可可王国旅行商人 — ReAct 智能体

## 语言

**默认语言为中文（简体）。** 仅当用户明确指定时才使用英文。

## 环境

- **项目根目录：** `/home/zyh/project/python3/pythontest/`
- **Python：** 3.14.4
- **虚拟环境：** `/home/zyh/project/python3/pythontest1/.venv/bin/activate`（注意是 `.venv` 不是 `venv`）
- **已安装依赖：** `requests`、`beautifulsoup4`、`lxml`、`openpyxl`、`python-docx`、`python-pptx`、`xlsxwriter`、`pillow`、`pytesseract`
- **API 密钥：** `export DEEPSEEK_API_KEY="sk-..."`（建议添加到 `~/.bashrc` 或 `~/.zshrc`）

## 架构（第三层 ReAct）

```
main.py → react_loop.py (run_react_agent) → llm_client.py → DeepSeek API
                                          → roco_tool.py (fetch_merchant) → 网页爬取
```

需创建的文件（按顺序）：
1. `llm_client.py` — 封装 `https://api.deepseek.com/v1/chat/completions`，签名：`chat(messages, model="deepseek-chat") → str`
2. `roco_tool.py` — `fetch_merchant() → str`，按优先级顺序尝试 3 个数据源
3. `react_loop.py` — `run_react_agent(query, tools, max_steps=5)`，解析 LLM JSON 响应（`thought|tool_call|final_answer`）
4. `config.py` — 添加 `LLM_MODEL`、`API_BASE_URL`、`MAX_STEPS`
5. `main.py` — 输入循环 → `run_react_agent()` → 输出响应
6. `memory.py` — 对话历史管理（`add_message`、`print_history`），由 main.py 调用

## 数据源（优先级顺序）

| # | URL | 说明 |
|---|-----|------|
| 1 | `rocokingdomworld.org/zh/merchant/` | 专用实时查询站，内嵌 JSON 数据。**最可靠。** |
| 2 | `onebiji.com/hykb_tools/comm/lkwgmerchant/preview.php?id=1` | 专用查询工具（注意：onebiji.com 首页是菜谱博客，实际工具在此子路径） |
| 3 | `gl.ali213.net` | 游戏攻略站（无直接商人数据，作为兜底搜索引擎） |
| *兜底* | 返回 `"无法获取商人数据"` | 全部失败 |

## 关键注意事项

- **时段（北京时间）：** 8-12 / 12-16 / 16-20 / 20-24 — 解析器必须判断当前时段以提供上下文
- **网站结构变更** 可能导致解析器失效 — 需要维护
- **LLM 可能输出格式错误的 JSON** — 在 ReAct 循环中实现重试或优雅降级
- **DeepSeek API 在中国大陆可直接访问**（无需 VPN）
- **未配置测试框架** — `pytest` 不在依赖中；通过 `python main.py` 手动测试

## 运行命令

```bash
source /home/zyh/project/python3/pythontest1/.venv/bin/activate
export DEEPSEEK_API_KEY="sk-..."
cd /home/zyh/project/python3/pythontest
python main.py
```

## LLM 响应 JSON 格式（ReAct）

```json
{"type": "thought", "content": "..."}
{"type": "tool_call", "tool": "fetch_merchant", "arguments": {}}
{"type": "final_answer", "content": "..."}
```
