import sys
from pathlib import Path

# 将项目根目录加入 sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from llm_toolkit.unified_llm_api import call_llm_api
from llm_toolkit.utils import get_providers


def test_all_providers():
    providers = get_providers()

    for provider in providers:
        print(f"\n🧩 测试 {provider} 模型")
        result = call_llm_api("向前走两秒", provider_name=provider)
        print(f"{provider}: {result}")


if __name__ == "__main__":
    test_all_providers()
