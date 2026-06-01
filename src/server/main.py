"""FastAPI 后端 + WebSocket：逐步推送 Pipeline 进度"""
import json
import traceback
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from src.data.seed_state import create_linan_state
from src.core.types import EventInput, AppraisalResult, MemoryRecallResult, ResponseDecision, ReplyOutput
from src.pipeline.appraisal import run_appraisal
from src.pipeline.memory_retrieval import retrieve_memory
from src.pipeline.response_decision import decide_response
from src.pipeline.prompt_generator import generate_expression_context
from src.pipeline.llm_client import call_text
from src.pipeline.state_updater import apply_state_updates

app = FastAPI(title="Virtual Human Flow")
linan_state = create_linan_state()


async def run_pipeline_with_progress(content: str, state, send):
    """逐步执行 pipeline，每步完成后通过 send 推送进度"""
    event = EventInput(
        id=f"evt_{datetime.utcnow().timestamp():.0f}",
        type="user_message", timestamp=datetime.utcnow(),
        speaker_id="user_b", speaker_name="B",
        room_id="main_room", content=content,
    )
    await send({"type": "step_progress", "step": "appraisal", "status": "running"})

    # Step 1
    appraisal_trace = await run_appraisal(event, state)
    await send({
        "type": "step_progress", "step": "appraisal", "status": "done",
        "trace": appraisal_trace.model_dump(mode="json"),
    })

    # Step 2
    await send({"type": "step_progress", "step": "memory", "status": "running"})
    appraisal_result = AppraisalResult(**appraisal_trace.output)
    memory_trace = await retrieve_memory(event, appraisal_result, state)
    await send({
        "type": "step_progress", "step": "memory", "status": "done",
        "trace": memory_trace.model_dump(mode="json"),
    })

    # Step 3
    await send({"type": "step_progress", "step": "decision", "status": "running"})
    memory_result = MemoryRecallResult(**memory_trace.output)
    decision_trace = await decide_response(appraisal_result, memory_result, state)
    await send({
        "type": "step_progress", "step": "decision", "status": "done",
        "trace": decision_trace.model_dump(mode="json"),
    })

    # Step 4: Prompt Generator
    await send({"type": "step_progress", "step": "prompt", "status": "running"})
    decision_result = ResponseDecision(**decision_trace.output)
    expression_ctx = generate_expression_context(
        event, state, appraisal_result, memory_result, decision_result,
    )
    await send({
        "type": "step_progress", "step": "prompt", "status": "done",
        "prompt": expression_ctx.prompt,
    })

    # Step 5: Reply LLM ← 不需要 JSON，纯文本
    await send({"type": "step_progress", "step": "reply", "status": "running"})
    reply_text = await call_text(expression_ctx.prompt)
    reply_output = ReplyOutput(reply=reply_text)
    await send({
        "type": "step_progress", "step": "reply", "status": "done",
        "reply": reply_text,
        "provider": expression_ctx.provider,
        "model": expression_ctx.model,
    })

    # Step 6: State Update
    await send({"type": "step_progress", "step": "state_update", "status": "running"})
    next_state, state_delta, state_update_trace = await apply_state_updates(
        state, event, reply_output, appraisal_result, memory_result, decision_result,
    )
    await send({
        "type": "step_progress", "step": "state_update", "status": "done",
        "trace": state_update_trace.model_dump(mode="json"),
        "state_delta": state_delta.model_dump(mode="json"),
    })

    # 最终推送事件和完整状态
    await send({
        "type": "final",
        "event": event.model_dump(mode="json"),
        "reply": reply_text,
        "state_delta": state_delta.model_dump(mode="json"),
    })

    return next_state


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global linan_state
    await ws.accept()

    async def send(msg):
        await ws.send_json(msg)

    await send({"type": "state_init", "data": linan_state.model_dump(mode="json")})

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "send_message":
                content = msg.get("content", "").strip()
                if not content:
                    continue

                try:
                    next_state = await run_pipeline_with_progress(content, linan_state, send)
                    linan_state = next_state
                    await send({"type": "state_update", "data": linan_state.model_dump(mode="json")})
                except Exception as e:
                    await send({
                        "type": "error",
                        "step": msg.get("current_step", "unknown"),
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                    })

            elif msg.get("type") == "reset":
                linan_state = create_linan_state()
                await send({"type": "state_init", "data": linan_state.model_dump(mode="json")})

    except WebSocketDisconnect:
        pass


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
