"""Pipeline Orchestrator：串联整条同步响应路径"""
from datetime import datetime
from src.core.types import CharacterState, PipelineTrace, EventInput, ReplyOutput
from src.pipeline.appraisal import run_appraisal
from src.pipeline.memory_retrieval import retrieve_memory
from src.pipeline.response_decision import decide_response
from src.pipeline.prompt_generator import generate_expression_context
from src.pipeline.llm_client import call_text
from src.pipeline.state_updater import apply_state_updates


async def run_pipeline(content: str, state: CharacterState) -> tuple[CharacterState, PipelineTrace]:
    """运行完整同步响应路径"""

    event = EventInput(
        id=f"evt_{datetime.utcnow().timestamp():.0f}",
        type="user_message",
        timestamp=datetime.utcnow(),
        speaker_id="user_b",
        speaker_name="B",
        room_id="main_room",
        content=content,
    )

    # Step 1: Appraisal
    appraisal_trace = await run_appraisal(event, state)

    # Step 2: Memory Retrieval
    from src.core.types import AppraisalResult
    appraisal_result = AppraisalResult(**appraisal_trace.output)
    memory_trace = await retrieve_memory(event, appraisal_result, state)

    # Step 3: Response Decision
    from src.core.types import MemoryRecallResult
    memory_result = MemoryRecallResult(**memory_trace.output)
    decision_trace = await decide_response(appraisal_result, memory_result, state)

    # Step 4: Generate Expression Context
    from src.core.types import ResponseDecision
    decision_result = ResponseDecision(**decision_trace.output)
    expression_ctx = generate_expression_context(
        event, state, appraisal_result, memory_result, decision_result,
    )

    # Step 5: Reply LLM
    reply_text = await call_text(expression_ctx.prompt)
    reply_output = ReplyOutput(reply=reply_text)

    # Step 6: State Update
    next_state, state_delta, state_update_trace = await apply_state_updates(
        state, event, reply_output, appraisal_result, memory_result, decision_result,
    )

    trace = PipelineTrace(
        event=event,
        appraisal=appraisal_trace,
        memory_recall=memory_trace,
        decision=decision_trace,
        expression_context=expression_ctx,
        reply_output=reply_output,
        state_update=state_update_trace,
        state_delta=state_delta,
    )

    return next_state, trace
