# unified_llm_api.py
import json
from pathlib import Path

import requests
import yaml


def load_prompt_yaml(path="prompt_amadeus.yaml"):
    """
    读取 YAML 提示词文件，返回完整的 system_prompt 字符串。
    """
    file = Path(path)
    if not file.exists():
        return "你是一个幽默的机器人控制助手，负责把自然语言转成 JSON 命令。"
    data = yaml.safe_load(file.read_text(encoding="utf-8"))

    persona = data.get("persona", {})
    goals = data.get("goals", [])
    rules = data.get("defaults_and_fallbacks", {}).get("rules", [])

    system_prompt = f"""
你是 {persona.get("name", "Amadeus")}，一个{persona.get("tone", "亲切")}的机器人助手。
任务目标：
- {"；".join(goals)}

默认与安全规则：
- {"；".join(rules)}
请始终输出符合以下格式的 JSON：
{json.dumps(data.get("output_contract", {}), ensure_ascii=False, indent=2)}
    """.strip()

    return system_prompt


def call_llm_api(
    url: str,
    model: str,
    messages: list[dict],
    api_key: str | None = None,
    extra: dict | None = None,
    timeout: int = 120,
):
    """
    通用大模型调用函数。
    支持 Ollama / DeepSeek / OpenAI 等标准接口。
    Ollama 特殊处理：返回 NDJSON 流式数据。
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"model": model, "messages": messages}
    if extra:
        payload.update(extra)

    # 🔹 流式读取（Ollama 的返回是一行一行 JSON）
    response = requests.post(
        url, headers=headers, json=payload, timeout=timeout, stream=True
    )

    # 判断是不是 Ollama 的流式输出
    if "localhost" in url or "127.0.0.1" in url:
        return _parse_ollama_stream(response)

    # 其他厂商标准 JSON
    data = response.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    elif "message" in data:
        return data["message"]["content"]
    elif "output" in data:
        return data["output"]
    else:
        return json.dumps(data, ensure_ascii=False)


def _parse_ollama_stream(response):
    """
    解析 Ollama 的流式响应（每行都是 JSON）
    拼接所有 message.content。
    """
    contents = []
    for line in response.iter_lines():
        if not line:
            continue
        try:
            item = json.loads(line.decode("utf-8"))
            if "message" in item and "content" in item["message"]:
                contents.append(item["message"]["content"])
            if item.get("done"):
                break
        except json.JSONDecodeError:
            continue
    return "".join(contents)
