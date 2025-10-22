from pathlib import Path

import toml

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR.parent / "config"
PROVIDER_PATH = CONFIG_DIR / "llm_provider.toml"


def get_providers() -> list[str]:
    """
    获取所有提供者
    """
    config = toml.load(PROVIDER_PATH)
    return list(config.keys())


if __name__ == "__main__":
    print(get_providers())
