"""Amadeus AI Backend - 机器人控制后端服务."""

import json
import os

import uvicorn
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger as lg

from schemas.command import AIResponse

# --- 配置变量 ---
ROBOT_WS_URL = os.getenv("ROBOT_WS_URL")
SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = os.getenv("SERVER_PORT")

# --- FastAPI 应用 ---
app = FastAPI(
    title="Amadeus AI Backend",
    description="机器人控制后端服务，支持 WebSocket 通信和 AI 指令处理",
    version="0.1.0",
)


async def handle_ai_output(ai_output_str: str) -> AIResponse | None:
    """处理 AI 输出并返回解析后的指令."""
    try:
        ai_result = AIResponse.model_validate_json(ai_output_str)
    except Exception as e:
        lg.error(f"AI 输出格式错误: {e}")
        return None

    lg.info(f"[AI说] {ai_result.text}")

    if ai_result.command:
        cmd = ai_result.command.fill_defaults()
        lg.info(
            f"[执行指令] {cmd.type} {cmd.direction or ''} "
            f"速度={cmd.speed}m/s 时间={cmd.duration}s 距离={cmd.distance}m"
        )
        return cmd
    return None


@app.websocket("/ws/control")
async def websocket_bridge(frontend_ws: WebSocket) -> None:
    """WebSocket 桥接端点，连接前端和机器人.

    这个端点桥接前端和机器人，同时管理两个 WebSocket 连接。
    """
    await frontend_ws.accept()
    lg.info("[Server] 前端应用已连接...")

    try:
        # 1. 作为 "客户端" 连接到树莓派机器人
        async with websockets.connect(ROBOT_WS_URL) as robot_ws:
            lg.info(f"[Server] 已成功连接到机器人: {ROBOT_WS_URL}")

            try:
                # 2. 创建一个 "双向转发" 循环
                while True:
                    # 等待前端发送指令
                    data_str = await frontend_ws.receive_text()

                    # (未来可以在这里加入 AI 逻辑)
                    # 比如：if data_str == "前进": data_str = json.dumps(...)

                    lg.info(f"[Server] 收到前端指令: {data_str}")

                    # 将指令原封不动地转发给机器人
                    await robot_ws.send(data_str)
                    lg.info("[Server] 已转发指令给机器人")

            except WebSocketDisconnect:
                lg.info("[Server] 前端应用已断开")
                # 安全保护：前端断开时，立即给机器人发送停止指令
                lg.warning("[Server] (安全) 发送 STOP 指令给机器人")
                await robot_ws.send(json.dumps({"action": "stop"}))

            except Exception as e:
                lg.error(f"[Server] 通信循环中出错: {e}")
                # 出现其他异常也发送停止指令
                if robot_ws.open:
                    await robot_ws.send(json.dumps({"action": "stop"}))

    except Exception as e:
        # 捕获连接到 "机器人" 时的失败
        lg.error(f"[Server] 严重错误：无法连接到机器人 {ROBOT_WS_URL}。错误: {e}")
        # 告诉前端我们无法连接到机器人
        await frontend_ws.close(code=1011, reason=f"无法连接到机器人: {e}")

    lg.info("[Server] 桥接会话结束")


@app.get("/")
def read_root() -> dict[str, str]:
    """健康检查端点."""
    return {"message": "Amadeus Windows AI Backend is running."}


def main() -> None:
    """启动服务的主函数."""
    # 加载环境变量
    load_dotenv()

    # 读取配置（带默认值）
    robot_ws_url = os.getenv("ROBOT_WS_URL", "ws://127.0.0.1:8765")
    server_host = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port = int(os.getenv("SERVER_PORT", "8000"))

    # 更新全局配置变量
    global ROBOT_WS_URL, SERVER_HOST, SERVER_PORT
    ROBOT_WS_URL = robot_ws_url
    SERVER_HOST = server_host
    SERVER_PORT = server_port

    lg.info("===============================")
    lg.info("🚀 Amadeus Windows AI 后端启动")
    lg.info(f"🌐 监听地址: http://{server_host}:{server_port}")
    lg.info(f"🤖 机器人目标: {robot_ws_url}")
    lg.info("===============================")

    uvicorn.run(app, host=server_host, port=server_port)


if __name__ == "__main__":
    main()
