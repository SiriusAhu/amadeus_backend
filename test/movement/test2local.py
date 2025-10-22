"""测试本地 Windows 后端的运动控制功能."""

import asyncio
import json

import websockets
from loguru import logger as lg

# 连接到本地的 Windows 后端，而不是机器人
URI = "ws://localhost:6300/ws/control"


async def send_command(
    ws: websockets.WebSocketServerProtocol, command: dict, duration: float = 1.5
) -> None:
    """发送指令并等待一段时间，然后停止.

    Args:
        ws: WebSocket 连接对象
        command: 要发送的指令字典
        duration: 指令执行持续时间（秒）
    """
    lg.info(f"-> (发往 Windows 后端): {command}")
    await ws.send(json.dumps(command))
    await asyncio.sleep(duration)

    lg.info("-> (发往 Windows 后端): 停止")
    await ws.send(json.dumps({"action": "stop"}))
    await asyncio.sleep(1.0)


async def run_test_suite() -> None:
    """运行完整的运动控制测试套件."""
    lg.info(f"--- 正在连接到 Windows 后端 {URI} ... ---")

    try:
        async with websockets.connect(URI) as ws:
            lg.success("--- 连接成功 ---")

            lg.info("\n--- 1. 测试前进 (linear_x = 0.8) ---")
            await send_command(ws, {"action": "move", "linear_x": 0.8})

            lg.info("\n--- 2. 测试后退 (linear_x = -0.8) ---")
            await send_command(ws, {"action": "move", "linear_x": -0.8})

            lg.info("\n--- 3. 测试左转 (angular_z = 0.8) ---")
            await send_command(ws, {"action": "move", "angular_z": 0.8})

            lg.info("\n--- 4. 测试右转 (angular_z = -0.8) ---")
            await send_command(ws, {"action": "move", "angular_z": -0.8})

            lg.success("\n--- 所有测试完成 ---")

    except Exception as e:
        lg.error("\n--- 连接失败或测试出错 ---")
        lg.error(f"错误: {e}")
        lg.info("请确保:")
        lg.info("  1. 树莓派上的 Docker 正在运行")
        lg.info("  2. `windows_backend.py` 脚本正在此电脑上运行")


if __name__ == "__main__":
    asyncio.run(run_test_suite())
