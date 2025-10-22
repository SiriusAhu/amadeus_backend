"""统一的 LLM API 调用模块，支持多种大模型提供商."""

import json
import os
from pathlib import Path

import requests
import toml
import yaml
from dotenv import load_dotenv
from loguru import logger as lg

# 自动加载 .env
load_dotenv()

# ===================== #
# 路径定义
# ===================== #
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR.parent / "config"
PROVIDER_PATH = CONFIG_DIR / "llm_provider.toml"
PROMPT_PATH = CONFIG_DIR / "prompt_amadeus.yaml"


def load_provider_config(provider_name: str = "ollama") -> dict[str, str | None]:
    """从配置文件加载 LLM 提供商配置.

    Args:
        provider_name: 提供商名称，默认为 "ollama"

    Returns:
        包含提供商配置的字典

    Raises:
        FileNotFoundError: 配置文件不存在
        KeyError: 指定的提供商不存在
    """
    if not PROVIDER_PATH.exists():
        msg = f"❌ 未找到配置文件: {PROVIDER_PATH}"
        lg.error(msg)
        raise FileNotFoundError(msg)

    config = toml.load(PROVIDER_PATH)

    if provider_name not in config:
        msg = f"⚠️ 配置文件中不存在 provider: {provider_name}"
        lg.error(msg)
        raise KeyError(msg)

    provider = config[provider_name]
    base_url = provider.get("base_url")
    model = provider.get("model")
    api_key_name = provider.get("api_key_name", "")
    api_key = os.getenv(api_key_name) if api_key_name else None

    lg.debug(f"加载提供商配置: {provider_name}")
    return {
        "provider": provider_name,
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
    }


def load_prompt_yaml(path: Path = PROMPT_PATH) -> str:
    """读取 YAML 提示词文件，返回完整的 system_prompt 字符串.

    Args:
        path: YAML 提示词文件路径

    Returns:
        格式化后的系统提示词字符串
    """
    file = Path(path)
    if not file.exists():
        default_prompt = "你是一个幽默的机器人控制助手，负责把自然语言转成 JSON 命令。"
        lg.warning(f"提示词文件不存在: {path}，使用默认提示词")
        return default_prompt

    try:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        lg.debug(f"成功加载提示词文件: {path}")
    except Exception as e:
        lg.error(f"读取提示词文件失败: {e}")
        return "你是一个幽默的机器人控制助手，负责把自然语言转成 JSON 命令。"

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
    text: str,
    provider_name: str = "ollama",
    extra: dict | None = None,
    timeout: int = 120,
) -> str:
    """通用大模型调用函数.

    自动从 llm_provider.toml 和 .env 中加载配置。
    自动加载 YAML 提示词。
    支持 Ollama / DeepSeek / OpenAI / ZhipuAI。

    Args:
        text: 用户输入文本
        provider_name: 提供商名称，默认为 "ollama"
        extra: 额外的请求参数
        timeout: 请求超时时间（秒）

    Returns:
        LLM 生成的响应文本

    Raises:
        requests.RequestException: 网络请求失败
        ValueError: 响应格式错误
    """
    lg.info(f"调用 LLM API: {provider_name}")
    lg.debug(f"用户输入: {text}")

    try:
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

        lg.debug(f"发送请求到: {url}")
        response = requests.post(
            url, headers=headers, json=payload, timeout=timeout, stream=True
        )
        response.raise_for_status()

        # Ollama: 流式 NDJSON
        if "localhost" in url or "127.0.0.1" in url:
            result = _parse_ollama_stream(response)
        else:
            # 标准 JSON（OpenAI / DeepSeek / ZhipuAI）
            data = response.json()
            if "choices" in data:
                result = data["choices"][0]["message"]["content"]
            elif "message" in data:
                result = data["message"]["content"]
            elif "output" in data:
                result = data["output"]
            else:
                result = json.dumps(data, ensure_ascii=False)

        lg.info(f"LLM 响应成功，长度: {len(result)} 字符")
        lg.debug(f"LLM 响应内容: {result}")
        return result

    except Exception as e:
        lg.error(f"LLM API 调用失败: {e}")
        raise


def _parse_ollama_stream(response: requests.Response) -> str:
    """解析 Ollama 的流式响应（每行都是 JSON）.

    Args:
        response: requests 响应对象

    Returns:
        拼接后的完整响应内容
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
            lg.warning(f"解析 Ollama 响应行失败: {line}")
            continue

    result = "".join(contents)
    lg.debug(f"Ollama 流式响应解析完成，内容长度: {len(result)}")
    return result
