import asyncio
import json

import websockets

# 我们现在连接到本地的 Windows 后端，而不是机器人
URI = "ws://localhost:6300/ws/control"


async def send_command(ws, command, duration=1.5):
    """发送指令并等待一段时间，然后停止"""
    print(f"-> (发往 Windows 后端): {command}")
    await ws.send(json.dumps(command))
    await asyncio.sleep(duration)

    print("-> (发往 Windows 后端): 停止")
    await ws.send(json.dumps({"action": "stop"}))
    await asyncio.sleep(1.0)


async def run_test_suite():
    print(f"--- 正在连接到 Windows 后端 {URI} ... ---")
    try:
        async with websockets.connect(URI) as ws:
            print("--- 连接成功 ---")

            print("\n--- 1. 测试前进 (linear_x = 0.8) ---")
            await send_command(ws, {"action": "move", "linear_x": 0.8})

            print("\n--- 2. 测试后退 (linear_x = -0.8) ---")
            await send_command(ws, {"action": "move", "linear_x": -0.8})

            print("\n--- 3. 测试左转 (angular_z = 0.8) ---")
            await send_command(ws, {"action": "move", "angular_z": 0.8})

            print("\n--- 4. 测试右转 (angular_z = -0.8) ---")
            await send_command(ws, {"action": "move", "angular_z": -0.8})

            print("\n--- 所有测试完成 ---")

    except Exception as e:
        print(f"\n--- 连接失败或测试出错 ---")
        print(f"错误: {e}")
        print("请确保:")
        print("  1. 树莓派上的 Docker 正在运行。")
        print("  2. `windows_backend.py` 脚本正在此电脑上运行。")


if __name__ == "__main__":
    asyncio.run(run_test_suite())
