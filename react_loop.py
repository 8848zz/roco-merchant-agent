import json
from config import MAX_STEPS
from llm_client import chat
from memory import get_history

SYSTEM_PROMPT = """你是洛可可王国旅行商人的查询助手。你可以使用工具获取数据，然后给出答案。

工具列表：
- fetch_merchant：获取当前旅行商人的商品信息，无参数。

你必须严格按照 JSON 格式输出，每行一个 JSON 对象。格式如下：
{"type": "thought", "content": "你的思考过程"}
{"type": "tool_call", "tool": "fetch_merchant", "arguments": {}}
{"type": "final_answer", "content": "你的最终回答"}

每次只能输出一个 JSON 对象。不要输出其他内容。"""


def run_react_agent(query, tools, max_steps=MAX_STEPS):
    tool_map = {t.__name__: t for t in tools}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    for step in range(max_steps):
        response = chat(messages)
        if response.startswith("错误："):
            return response

        response = response.strip()
        lines = response.splitlines()
        objs = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                objs.append(json.loads(line))
            except json.JSONDecodeError:
                try:
                    start = line.index("{")
                    end = line.rindex("}") + 1
                    objs.append(json.loads(line[start:end]))
                except (ValueError, json.JSONDecodeError):
                    continue

        if not objs:
            messages.append({
                "role": "user",
                "content": f"你的输出格式错误（不是有效 JSON）：{response}。请只输出 JSON 格式的响应。"
            })
            continue

        for obj in objs:
            action_type = obj.get("type")
            if action_type == "thought":
                continue

            if action_type == "tool_call":
                tool_name = obj.get("tool")
                if tool_name in tool_map:
                    result = tool_map[tool_name]()
                    messages.append({
                        "role": "user",
                        "content": f"Observation: {result}"
                    })
                else:
                    messages.append({
                        "role": "user",
                        "content": f"未知工具：{tool_name}。可用工具：{list(tool_map.keys())}"
                    })
                break

            if action_type == "final_answer":
                return obj.get("content", "")

            messages.append({
                "role": "user",
                "content": f"未知 action_type：{action_type}。有效类型：thought, tool_call, final_answer"
            })

    return "错误：已超过最大推理步数，未能得出答案。"
