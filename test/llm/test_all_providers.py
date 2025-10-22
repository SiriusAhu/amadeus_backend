"""测试所有 LLM 提供商的功能."""

import sys
from pathlib import Path

from loguru import logger as lg

# 将项目根目录加入 sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from llm_toolkit.unified_llm_api import call_llm_api
from llm_toolkit.utils import get_providers


def test_all_providers() -> None:
    """测试所有配置的 LLM 提供商."""
    lg.info("开始测试所有 LLM 提供商")

    try:
        providers = get_providers()
        test_prompt = "向前走两秒"

        for provider in providers:
            lg.info(f"🧩 测试 {provider} 模型")
            try:
                result = call_llm_api(test_prompt, provider_name=provider)
                lg.success(f"{provider} 测试成功")
                print(f"{provider}: {result}")
            except Exception as e:
                lg.error(f"{provider} 测试失败: {e}")

    except Exception as e:
        lg.error(f"测试过程中发生错误: {e}")


if __name__ == "__main__":
    test_all_providers()
