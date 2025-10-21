import json
import websockets  # 用来实现 "客户端" 功能
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import os

# --- 配置 ---
# 您树莓派小车的 WebSocket 地址
ROBOT_WS_URL = os.getenv("ROBOT_WS_URL")

SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = os.getenv("SERVER_PORT")

# --- FastAPI 应用 ---
app = FastAPI()

@app.websocket("/ws/control")
async def websocket_bridge(frontend_ws: WebSocket):
    """
    这个端点桥接前端和机器人。
    它会同时管理两个 WebSocket 连接。
    """
    await frontend_ws.accept()
    print("[Server] 前端应用已连接...")

    try:
        # 1. 作为 "客户端" 连接到树莓派机器人
        async with websockets.connect(ROBOT_WS_URL) as robot_ws:
            print(f"[Server] 已成功连接到机器人: {ROBOT_WS_URL}")

            try:
                # 2. 创建一个 "双向转发" 循环
                while True:
                    # 等待前端发送指令
                    data_str = await frontend_ws.receive_text()
                    
                    # (未来您可以在这里加入 AI 逻辑)
                    # 比如：if data_str == "前进": data_str = json.dumps(...)
                    
                    print(f"[Server] 收到前端指令: {data_str}")
                    
                    # 将指令原封不动地转发给机器人
                    await robot_ws.send(data_str)
                    print(f"[Server] 已转发指令给机器人。")

            except WebSocketDisconnect:
                print("[Server] 前端应用已断开。")
                # 安全保护：前端断开时，立即给机器人发送停止指令
                print("[Server] (安全) 发送 STOP 指令给机器人。")
                await robot_ws.send(json.dumps({"action": "stop"}))
            
            except Exception as e:
                print(f"[Server] 通信循环中出错: {e}")
                # 出现其他异常也发送停止指令
                if robot_ws.open:
                    await robot_ws.send(json.dumps({"action": "stop"}))

    except Exception as e:
        # 捕获连接到 "机器人" 时的失败
        print(f"[Server] 严重错误：无法连接到机器人 {ROBOT_WS_URL}。错误: {e}")
        # 告诉前端我们无法连接到机器人
        await frontend_ws.close(code=1011, reason=f"无法连接到机器人: {e}")

    print("[Server] 桥接会话结束。")


@app.get("/")
def read_root():
    return {"message": "Amadeus Windows AI Backend is running."}

# --- 启动服务 ---
if __name__ == "__main__":
    print(f"--- Amadeus Windows AI 后端启动 ---")
    print(f"--- 监听地址: http://{SERVER_HOST}:{SERVER_PORT} ---")
    print(f"--- 机器人目标: {ROBOT_WS_URL} ---")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)