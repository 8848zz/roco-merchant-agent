# 洛可可王国旅行商人 Agent

查询《洛克王国》远行商人商品信息的 ReAct 智能体，支持 CLI 对话查询和微信定时推送。

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
    pip install -r requirements.txt
export DEEPSEEK_API_KEY="sk-..."
python main.py
```

## 功能

- **CLI 查询** — 输入自然语言查询商品信息，如"中午卖什么"、"第四轮有什么"
- **定时推送** — cron-job.org 每天 8 次推送（08:05/09:05/12:05/13:05/16:05/17:05/20:05/21:05）到微信（Server酱）

## 架构

```
main.py → react_loop.py → llm_client.py → DeepSeek API
                          → roco_tool.py → rocokingdomworld.org（主）
                                         → onebiji.com（备）
                                         → ali213.net（兜底）
```

## 数据源

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | rocokingdomworld.org/zh/merchant/ | 内嵌 JSON，最可靠 |
| 2 | onebiji.com/hykb_tools/... | HTML 解析，CSS 类划分轮次 |
| 3 | gl.ali213.net | 攻略站，无结构化数据，兜底 |

## 定时推送配置

在 [cron-job.org](https://cron-job.org) 创建 8 个任务，每个任务：

| 字段 | 值 |
|------|-----|
| URL | `https://api.github.com/repos/8848zz/roco-merchant-agent/actions/workflows/merchant.yml/dispatches` |
| Method | `POST` |
| Content-Type | `application/json` |
| Body | `{"ref":"main"}` |
| Header | `Authorization: Bearer <GitHub PAT>` |

8 个时间点（时区选 Asia/Shanghai）：08:05 / 09:05 / 12:05 / 13:05 / 16:05 / 17:05 / 20:05 / 21:05

GitHub Secrets 需要：
- `SERVERCHAN_SENDKEY` — [Server酱](https://sct.ftqq.com) 的 SendKey
- `GH_PAT` — GitHub Personal Access Token（权限需勾 `workflow`）

## 许可证

MIT
