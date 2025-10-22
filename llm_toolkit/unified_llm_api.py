# unified_llm_api.py
import json
import os
from pathlib import Path

import requests
import toml
import yaml
from dotenv import load_dotenv

# 自动加载 .env
load_dotenv()

# ===================== #
# 路径定义
# ===================== #
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR.parent / "config"
PROVIDER_PATH = CONFIG_DIR / "llm_provider.toml"
PROMPT_PATH = CONFIG_DIR / "prompt_amadeus.yaml"


# ===================== #
# 读取 TOML 配置
# ===================== #
def load_provider_config(provider_name="ollama"):
    """
    从 ../config/llm_provider.toml 加载 provider 配置
    """
    if not PROVIDER_PATH.exists():
        raise FileNotFoundError(f"❌ 未找到配置文件: {PROVIDER_PATH}")
    config = toml.load(PROVIDER_PATH)

    if provider_name not in config:
        raise KeyError(f"⚠️ 配置文件中不存在 provider: {provider_name}")

    provider = config[provider_name]
    base_url = provider.get("base_url")
    model = provider.get("model")
    api_key_name = provider.get("api_key_name", "")
    api_key = os.getenv(api_key_name) if api_key_name else None

    return {
        "provider": provider_name,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
    }


# ===================== #
# 读取 YAML 提示词
# ===================== #
def load_prompt_yaml(path=PROMPT_PATH):
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


# ===================== #
# 通用 LLM 请求
# ===================== #
def call_llm_api(
    text: str,
    provider_name: str = "ollama",
    extra: dict | None = None,
    timeout: int = 120,
):
    """
    通用大模型调用函数。
    自动从 llm_provider.toml 和 .env 中加载配置。
    自动加载 YAML 提示词。
    支持 Ollama / DeepSeek / OpenAI / ZhipuAI。
    """
    config = load_provider_config(provider_name)
    url = config["base_url"]
    model = config["model"]
    api_key = config["api_key"]

    system_prompt = load_prompt_yaml()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    }
    if extra:
        payload.update(extra)

    response = requests.post(
        url, headers=headers, json=payload, timeout=timeout, stream=True
    )

    # Ollama: 流式 NDJSON
    if "localhost" in url or "127.0.0.1" in url:
        return _parse_ollama_stream(response)

    # 标准 JSON（OpenAI / DeepSeek / ZhipuAI）
    data = response.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    elif "message" in data:
        return data["message"]["content"]
    elif "output" in data:
        return data["output"]
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
