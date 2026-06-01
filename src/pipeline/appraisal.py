"""Appraisal 路由层：判断事件触发了哪些关切"""
import json
from src.core.types import (
    AppraisalResult, ActivatedConcern, CognitiveModuleTrace,
    CognitiveModuleRequest, CognitiveModuleName, EventInput, CharacterState,
)
from src.pipeline.llm_client import call_json


def build_appraisal_prompt(event: EventInput, state: CharacterState) -> str:
    concerns_desc = []
    for c in state.concerns:
        if c.status == "active":
            concerns_desc.append(
                f"- concern_id: {c.id}\n"
                f"  title: {c.title}\n"
                f"  triggers: {c.triggers}\n"
                f"  current_intensity: {c.intensity}\n"
                f"  current_valence: {c.valence}"
            )
    concerns_text = "\n".join(concerns_desc) if concerns_desc else "（无活跃关切）"

    speaker_id = event.speaker_id or "unknown"
    rel = state.relationships.get(speaker_id)
    rel_text = "（陌生人，无关系档案）"
    if rel:
        rel_text = (
            f"familiarity={rel.familiarity}, trust={rel.trust}, "
            f"affection={rel.affection}, tension={rel.tension}, "
            f"recent_tone: {rel.recent_tone}"
        )

    return (
        f"你是虚拟角色「{state.profile.name}」的认知评估模块。"
        f"请判断以下事件是否触发了她的任何关切。\n\n"
        f"事件内容：\"{event.content}\"\n"
        f"说话者：{speaker_id}（{rel_text}）\n\n"
        f"当前活跃关切：\n{concerns_text}\n\n"
        f"请分析事件是否命中任何关切的 trigger，并输出 JSON：\n"
        f'{{"activated_concerns": ['
        f'{{"concern_id": "string", "activation_score": 0.0-1.0, "matched_triggers": ["string"], "reason": "string"}}'
        f'], "event_salience": 0.0-1.0, "appraisal_summary": "string"}}\n'
        f"如果没有命中任何关切，activated_concerns 为空数组。"
    )


async def run_appraisal(event: EventInput, state: CharacterState) -> CognitiveModuleTrace:
    prompt = build_appraisal_prompt(event, state)
    schema_hint = (
        "Output: {\"activated_concerns\": [{\"concern_id\":\"\",\"activation_score\":0.0,"
        "\"matched_triggers\":[],\"reason\":\"\"}],\"event_salience\":0.0,\"appraisal_summary\":\"\"}"
    )

    output = await call_json(prompt, schema_hint)

    activated = [
        ActivatedConcern(
            concern_id=ac.get("concern_id", ""),
            activation_score=float(ac.get("activation_score", 0)),
            matched_triggers=ac.get("matched_triggers", []),
            reason=ac.get("reason", ""),
        )
        for ac in output.get("activated_concerns", [])
    ]

    result = AppraisalResult(
        event_id=event.id,
        activated_concerns=activated,
        event_salience=float(output.get("event_salience", 0)),
        appraisal_summary=output.get("appraisal_summary", ""),
    )

    return CognitiveModuleTrace(
        module_name=CognitiveModuleName.APPRAISAL,
        request=CognitiveModuleRequest(
            module_name=CognitiveModuleName.APPRAISAL,
            input_mode="structured_context",
            output_mode="structured_json",
            prompt=prompt,
            output_contract='{"activated_concerns": [...], "event_salience": 0.0, "appraisal_summary": ""}',
        ),
        output=result.model_dump(),
    )
