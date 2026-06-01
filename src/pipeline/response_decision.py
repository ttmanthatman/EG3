"""Response Decision：在 LLM 开口前先决定是否回应、怎么回应"""
from src.core.types import (
    ResponseDecision, ResponseMode, CognitiveModuleTrace,
    CognitiveModuleRequest, CognitiveModuleName, AppraisalResult,
    MemoryRecallResult, CharacterState,
)
from src.pipeline.llm_client import call_json


def build_decision_prompt(
    appraisal: AppraisalResult, recall: MemoryRecallResult, state: CharacterState
) -> str:
    mood = state.runtime.derived_mood
    energy = state.runtime.energy
    active_concerns_text = ", ".join(
        [f"{ac.concern_id}(score={ac.activation_score:.1f})" for ac in appraisal.activated_concerns]
    ) if appraisal.activated_concerns else "无"

    return (
        f"你是虚拟角色「{state.profile.name}」的响应决策模块。\n"
        f"当前事件显著性：{appraisal.event_salience:.2f}\n"
        f"激活的关切：{active_concerns_text}\n"
        f"当前心情：{mood.label}（valence={mood.valence:.1f}, arousal={mood.arousal:.1f}）\n"
        f"精力：{energy:.1f}\n"
        f"评估摘要：{appraisal.appraisal_summary}\n\n"
        f"请决定她的回应姿态。可选模式：warm_reply / neutral_reply / short_avoidance / "
        f"topic_shift / question_back / silence / delayed_reply / emotional_outburst\n"
        f"输出 JSON：\n"
        f'{{"should_respond": true/false, "response_mode": "模式", '
        f'"delay_seconds": null或秒数, "rationale": "决策理由"}}'
    )


async def decide_response(
    appraisal: AppraisalResult, recall: MemoryRecallResult, state: CharacterState
) -> CognitiveModuleTrace:
    prompt = build_decision_prompt(appraisal, recall, state)
    schema_hint = (
        'Output: {"should_respond": true/false, "response_mode": "neutral_reply|short_avoidance|...", '
        '"delay_seconds": null or number, "rationale": "..."}'
    )

    output = await call_json(prompt, schema_hint)

    mode_str = output.get("response_mode", "neutral_reply")
    try:
        mode = ResponseMode(mode_str)
    except ValueError:
        mode = ResponseMode.NEUTRAL_REPLY

    result = ResponseDecision(
        should_respond=output.get("should_respond", True),
        response_mode=mode,
        delay_seconds=output.get("delay_seconds"),
        rationale=output.get("rationale", ""),
    )

    return CognitiveModuleTrace(
        module_name=CognitiveModuleName.RESPONSE_DECISION,
        request=CognitiveModuleRequest(
            module_name=CognitiveModuleName.RESPONSE_DECISION,
            input_mode="structured_context",
            output_mode="structured_json",
            prompt=prompt,
            output_contract='{"should_respond": bool, "response_mode": "string", "delay_seconds": null, "rationale": "string"}',
        ),
        output=result.model_dump(),
    )
