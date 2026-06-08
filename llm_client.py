import os
import requests
from config import API_BASE_URL, LLM_MODEL

TIMEOUT = 60

def chat(messages, model=LLM_MODEL):
    url = f"{API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('DEEPSEEK_API_KEY', '')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "错误：API 请求超时"
    except requests.exceptions.RequestException as e:
        return f"错误：API 请求失败 — {e}"
    except (KeyError, ValueError) as e:
        return f"错误：API 响应解析失败 — {e}"
