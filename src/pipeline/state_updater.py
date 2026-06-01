"""State Updater：根据回复和上下文判断状态变化，并确定性写回"""
import copy
from datetime import datetime
from src.core.types import (
    CharacterState, EventInput, ReplyOutput, StateUpdatePlan,
    ConcernUpdate, RelationshipUpdate, NewConcern,
    CognitiveModuleTrace, CognitiveModuleRequest, CognitiveModuleName,
    StateDelta, ShortTermMemory, LongTermMemory, ConcernStatus,
    AppraisalResult, MemoryRecallResult, ResponseDecision,
)
from src.pipeline.llm_client import call_json


def build_state_update_prompt(
    state: CharacterState,
    event: EventInput,
    reply: ReplyOutput,
    appraisal: AppraisalResult,
    recall: MemoryRecallResult,
    decision: ResponseDecision,
) -> str:
    active_ids = [ac.concern_id for ac in appraisal.activated_concerns]
    speaker_id = event.speaker_id or "unknown"

    return (
        f"你是虚拟角色「{state.profile.name}」的状态更新模块。\n"
        f"刚刚发生了一次对话：\n"
        f"对方说：「{event.content}」\n"
        f"她回应：「{reply.reply}」\n"
        f"激活的关切：{active_ids}\n"
        f"决策模式：{decision.response_mode.value}\n"
        f"评估摘要：{appraisal.appraisal_summary}\n\n"
        f"请判断这次互动对她的状态产生了什么变化。输出 JSON：\n"
        f'{{"concern_updates": [{{"concern_id":"","intensity_delta":±0.05,"valence_delta":±0.05,"'
        f'"arousal_delta":±0.05,"note":""}}],'
        f'"relationship_updates": [{{"target_id":"","familiarity_delta":±0.02,"trust_delta":±0.02,'
        f'"affection_delta":±0.02,"tension_delta":±0.02,"note":""}}],'
        f'"new_concerns": [],'
        f'"internal_state_note": "她在心里想但没有说出来的话"}}'
    )


async def apply_state_updates(
    state: CharacterState,
    event: EventInput,
    reply: ReplyOutput,
    appraisal: AppraisalResult,
    recall: MemoryRecallResult,
    decision: ResponseDecision,
) -> tuple[CharacterState, StateDelta, CognitiveModuleTrace]:
    prompt = build_state_update_prompt(state, event, reply, appraisal, recall, decision)
    schema_hint = (
        'Output: {"concern_updates": [...], "relationship_updates": [...], '
        '"new_concerns": [...], "internal_state_note": "..."}'
    )

    output = await call_json(prompt, schema_hint)

    updates = []

    # 解析状态更新计划
    for cu in output.get("concern_updates", []):
        updates.append(ConcernUpdate(
            concern_id=cu.get("concern_id", ""),
            intensity_delta=cu.get("intensity_delta"),
            valence_delta=cu.get("valence_delta"),
            arousal_delta=cu.get("arousal_delta"),
            note=cu.get("note", ""),
        ))
    for ru in output.get("relationship_updates", []):
        updates.append(RelationshipUpdate(
            target_id=ru.get("target_id", ""),
            familiarity_delta=ru.get("familiarity_delta"),
            trust_delta=ru.get("trust_delta"),
            affection_delta=ru.get("affection_delta"),
            tension_delta=ru.get("tension_delta"),
            note=ru.get("note", ""),
        ))
    new_concerns_raw = output.get("new_concerns", [])
    internal_note = output.get("internal_state_note", "")

    plan = StateUpdatePlan(
        concern_updates=[u for u in updates if isinstance(u, ConcernUpdate)],
        relationship_updates=[u for u in updates if isinstance(u, RelationshipUpdate)],
        new_concerns=[NewConcern(**nc) for nc in new_concerns_raw],
        internal_state_note=internal_note,
    )

    # 确定性写回
    next_state = copy.deepcopy(state)
    state_delta = StateDelta()

    # 写回关切变化
    for cu in plan.concern_updates:
        for c in next_state.concerns:
            if c.id == cu.concern_id:
                if cu.intensity_delta is not None:
                    c.intensity = max(0.0, min(1.0, c.intensity + cu.intensity_delta))
                if cu.valence_delta is not None:
                    c.valence = max(-1.0, min(1.0, c.valence + cu.valence_delta))
                if cu.arousal_delta is not None:
                    c.arousal = max(0.0, min(1.0, c.arousal + cu.arousal_delta))
                if cu.status:
                    c.status = cu.status
                c.last_activated_at = datetime.utcnow()
                state_delta.concern_changes.append(f"{c.title}: {cu.note}")
                break

    # 写回关系变化
    for ru in plan.relationship_updates:
        if ru.target_id in next_state.relationships:
            rel = next_state.relationships[ru.target_id]
            if ru.familiarity_delta is not None:
                rel.familiarity = max(0.0, min(1.0, rel.familiarity + ru.familiarity_delta))
            if ru.trust_delta is not None:
                rel.trust = max(0.0, min(1.0, rel.trust + ru.trust_delta))
            if ru.affection_delta is not None:
                rel.affection = max(-1.0, min(1.0, rel.affection + ru.affection_delta))
            if ru.tension_delta is not None:
                rel.tension = max(0.0, min(1.0, rel.tension + ru.tension_delta))
            rel.last_interaction_at = datetime.utcnow()
            state_delta.relationship_changes.append(f"与{rel.target_name}: {ru.note}")

    # 添加新关切
    for nc in plan.new_concerns:
        import uuid
        new_c = type(next_state.concerns[0]) if next_state.concerns else type('Concern', (), {})
        new_concern = ConcernStatus.ACTIVE  # placeholder
        state_delta.concern_changes.append(f"新增关切: {nc.title}")

    # 写入短期记忆
    next_state.short_term_memory.append(ShortTermMemory(
        id=f"stm_{event.id}_user",
        timestamp=event.timestamp,
        speaker_id=event.speaker_id or "unknown",
        speaker_name=event.speaker_name or "?",
        content=event.content,
        event_id=event.id,
    ))
    next_state.short_term_memory.append(ShortTermMemory(
        id=f"stm_{event.id}_persona",
        timestamp=datetime.utcnow(),
        speaker_id=state.profile.id,
        speaker_name=state.profile.name,
        content=reply.reply,
        event_id=event.id,
    ))
    state_delta.memory_writes.append(f"写入2条短期记忆")

    # 内心活动写入长期记忆
    if internal_note:
        import uuid as _uuid
        next_state.long_term_memory.append(LongTermMemory(
            id=f"ltm_{_uuid.uuid4().hex[:8]}",
            summary=internal_note,
            related_people=[event.speaker_id or "unknown"],
            related_concerns=[ac.concern_id for ac in appraisal.activated_concerns],
            emotional_valence=state.runtime.derived_mood.valence,
            emotional_intensity=appraisal.event_salience,
            importance=0.4,
        ))
        state_delta.memory_writes.append(f"内心活动入库")

    # 更新运行时
    next_state.runtime.last_active_at = datetime.utcnow()
    next_state.runtime.energy = max(0.05, next_state.runtime.energy - 0.02)

    trace = CognitiveModuleTrace(
        module_name=CognitiveModuleName.STATE_UPDATE,
        request=CognitiveModuleRequest(
            module_name=CognitiveModuleName.STATE_UPDATE,
            input_mode="structured_context",
            output_mode="structured_json",
            prompt=prompt,
            output_contract='{"concern_updates": [...], "relationship_updates": [...], ...}',
        ),
        output=plan.model_dump(),
    )

    return next_state, state_delta, trace
