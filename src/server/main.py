"""FastAPI 后端 + WebSocket：接收消息 → 运行 Pipeline → 实时推送 trace"""
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.pipeline.orchestrator import run_pipeline
from src.data.seed_state import create_linan_state

app = FastAPI(title="Virtual Human Flow")

# 全局状态（MVP 单会话）
linan_state = create_linan_state()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global linan_state
    await ws.accept()

    # 发送初始状态
    await ws.send_json({
        "type": "state_init",
        "data": linan_state.model_dump(mode="json"),
    })

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "send_message":
                content = msg.get("content", "")
                if not content.strip():
                    continue

                # 发送状态：开始处理
                await ws.send_json({"type": "processing", "step": "start"})

                try:
                    next_state, trace = await run_pipeline(content, linan_state)
                    linan_state = next_state
                except Exception as e:
                    await ws.send_json({
                        "type": "error",
                        "message": str(e),
                    })
                    continue

                # 推送完整的 Pipeline Trace
                await ws.send_json({
                    "type": "pipeline_trace",
                    "data": trace.model_dump(mode="json"),
                })

                # 推送更新后的状态
                await ws.send_json({
                    "type": "state_update",
                    "data": linan_state.model_dump(mode="json"),
                })

            elif msg.get("type") == "reset":
                linan_state = create_linan_state()
                await ws.send_json({
                    "type": "state_init",
                    "data": linan_state.model_dump(mode="json"),
                })

    except WebSocketDisconnect:
        pass


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
