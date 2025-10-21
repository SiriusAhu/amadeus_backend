import json

import yaml
from ollama import chat

# === 读取 Prompt 规范 ===
with open("prompt_amadeus.yaml", "r", encoding="utf-8") as f:
    prompt_yaml = yaml.safe_load(f)

# 将 YAML 格式转成系统提示（简洁可读）
system_prompt = f"""
你现在是 {prompt_yaml["persona"]["name"]}，一个{prompt_yaml["persona"]["tone"]} 的机器人助手。

任务目标：
- 根据用户自然语言生成结构化命令（JSON）。
- 若不确定或参数不全，输出 stop 命令。
- 所有输出必须是 JSON，遵守以下约束：
  {json.dumps(prompt_yaml["output_contract"], ensure_ascii=False, indent=2)}
"""

# === 调用 Ollama 模型 ===
MODEL = "qwen2.5:3b"  # 你也可以换成 qwen2, gemma2, mistral 等本地模型
user_input = "向前走两秒钟，慢一点"

response = chat(
    model=MODEL,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ],
)

# === 打印原始输出 ===
print("\n--- 模型原始输出 ---")
print(response["message"]["content"])

# === 尝试解析 JSON ===
try:
    data = json.loads(response["message"]["content"])
    print("\n--- 解析成功 ✅ ---")
    print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print("\n--- ⚠️ 解析失败 ---")
    print("错误:", e)
