"""LLM 工具包的实用函数."""

from pathlib import Path

import toml
from loguru import logger as lg

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR.parent / "config"
PROVIDER_PATH = CONFIG_DIR / "llm_provider.toml"


def get_providers() -> list[str]:
    """获取所有可用的 LLM 提供商.

    Returns:
        提供商名称列表

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    if not PROVIDER_PATH.exists():
        msg = f"配置文件不存在: {PROVIDER_PATH}"
        lg.error(msg)
        raise FileNotFoundError(msg)

    try:
        config = toml.load(PROVIDER_PATH)
        providers = list(config.keys())
        lg.info(f"找到 {len(providers)} 个提供商: {providers}")
        return providers
    except Exception as e:
        lg.error(f"读取提供商配置失败: {e}")
        raise


if __name__ == "__main__":
    providers = get_providers()
    print(f"可用提供商: {providers}")
