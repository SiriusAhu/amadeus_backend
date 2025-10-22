import asyncio
import json

import websockets

URI = "ws://192.168.31.201:8000/ws"


async def send_command(ws, command, duration=1.5):
    """发送指令并等待一段时间，然后停止"""
    print(f"-> 发送指令: {command}")
    await ws.send(json.dumps(command))
    await asyncio.sleep(duration)

    print("-> 发送停止")
    await ws.send(json.dumps({"action": "stop"}))
    await asyncio.sleep(1.0)  # 停止后等待1秒，用于观察


async def run_test_suite():
    print(f"--- 正在连接到 {URI} ... ---")
    try:
        async with websockets.connect(URI) as ws:
            print("--- 连接成功 ---")

            # === 第1组：前进/后退 (linear_x) ===
            print("\n--- 1. 测试前进 (linear_x = 0.8) ---")
            await send_command(ws, {"action": "move", "linear_x": 0.8})

            print("\n--- 2. 测试后退 (linear_x = -0.8) ---")
            await send_command(ws, {"action": "move", "linear_x": -0.8})

            # === 第2组：左转/右转 (angular_z) ===
            # 这是我们重点观察的
            print("\n--- 3. 测试左转 (angular_z = 0.8) ---")
            await send_command(ws, {"action": "move", "angular_z": 0.8})

            print("\n--- 4. 测试右转 (angular_z = -0.8) ---")
            await send_command(ws, {"action": "move", "angular_z": -0.8})

            print("\n--- 所有测试完成 ---")

    except Exception as e:
        print("\n--- 连接失败或测试出错 ---")
        print(f"错误: {e}")
        print("请确保树莓派上的 Docker 容器正在运行。")


if __name__ == "__main__":
    asyncio.run(run_test_suite())
