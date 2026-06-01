"""Memory Retrieval：判断哪些记忆会在此刻浮现"""
from src.core.types import (
    MemoryRecallResult, RecalledMemory, CognitiveModuleTrace,
    CognitiveModuleRequest, CognitiveModuleName, EventInput, CharacterState,
    AppraisalResult,
)
from src.pipeline.llm_client import call_json


def build_memory_prompt(event: EventInput, appraisal: AppraisalResult, state: CharacterState) -> str:
    short_text = "\n".join(
        [f"[{m.speaker_name}]: {m.content}" for m in state.short_term_memory[-5:]]
    ) if state.short_term_memory else "（无）"

    long_list = []
    for m in state.long_term_memory:
        long_list.append(f"- [{m.id}] {m.summary} (emotional_intensity={m.emotional_intensity}, related_people={m.related_people}, related_concerns={m.related_concerns})")
    long_text = "\n".join(long_list) if long_list else "（无长期记忆）"

    activated_ids = [ac.concern_id for ac in appraisal.activated_concerns]
    speaker_id = event.speaker_id or ""

    return (
        f"你是虚拟角色「{state.profile.name}」的记忆召回模块。\n"
        f"当前事件触发了这些关切：{activated_ids}。\n"
        f"说话者是：{speaker_id}。\n\n"
        f"短期记忆（最近对话）：\n{short_text}\n\n"
        f"长期记忆库：\n{long_text}\n\n"
        f"请判断哪些长期记忆会在她此刻浮现。评分考虑：相关性 + 情绪强度 + 与说话者的关系。\n"
        f"只取最相关的 3 条。输出 JSON：\n"
        f'{{"long_term_memories": ['
        f'{{"memory_id": "string", "summary": "string", "score": 0.0-1.0, "reason": "string"}}'
        f']}}'
    )


async def retrieve_memory(
    event: EventInput, appraisal: AppraisalResult, state: CharacterState
) -> CognitiveModuleTrace:
    prompt = build_memory_prompt(event, appraisal, state)
    schema_hint = (
        'Output: {"long_term_memories": [{"memory_id":"","summary":"","score":0.0,"reason":""}]}.'
        ' Output 3 most relevant memories. If none relevant, return empty array.'
    )

    output = await call_json(prompt, schema_hint)

    recalled = [
        RecalledMemory(
            memory_id=m.get("memory_id", ""),
            summary=m.get("summary", ""),
            score=float(m.get("score", 0)),
            reason=m.get("reason", ""),
        )
        for m in output.get("long_term_memories", [])
    ]

    result = MemoryRecallResult(
        short_term_context=state.short_term_memory[-6:] if state.short_term_memory else [],
        long_term_memories=recalled,
    )

    return CognitiveModuleTrace(
        module_name=CognitiveModuleName.MEMORY_RETRIEVAL,
        request=CognitiveModuleRequest(
            module_name=CognitiveModuleName.MEMORY_RETRIEVAL,
            input_mode="structured_context",
            output_mode="structured_json",
            prompt=prompt,
            output_contract='{"long_term_memories": [...]}',
        ),
        output=result.model_dump(),
    )
