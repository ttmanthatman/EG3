"""Prompt Generator：把认知模块的输出转成纯自然语言上下文，只给 Reply LLM 使用"""
from src.core.types import (
    EventInput, CharacterState, AppraisalResult, MemoryRecallResult,
    ResponseDecision, ExpressionContext,
)
from src.config import DEEPSEEK_MODEL


def generate_expression_context(
    event: EventInput,
    state: CharacterState,
    appraisal: AppraisalResult,
    recall: MemoryRecallResult,
    decision: ResponseDecision,
) -> ExpressionContext:
    """生成只含自然语言的回复上下文——不含 JSON/字段名/工程术语"""

    # 激活的关切叙述
    concern_lines = []
    for ac in appraisal.activated_concerns:
        for c in state.concerns:
            if c.id == ac.concern_id:
                concern_lines.append(
                    f"她心里有一件在意的事：{c.title}。{c.description}"
                    f"这件事的强度是{c.intensity:.1f}。{ac.reason}"
                )
                break

    # 记忆叙述
    memory_lines = []
    for m in recall.long_term_memories:
        memory_lines.append(f"她此刻想起了一件事：{m.summary}")

    # 关系叙述
    speaker_id = event.speaker_id or "unknown"
    rel = state.relationships.get(speaker_id)
    if rel:
        rel_text = (
            f"说话的人是{rel.target_name}。"
            f"她对{rel.target_name}的熟悉程度是{rel.familiarity:.1f}，"
            f"信任度{rel.trust:.1f}，好感{rel.affection:.1f}。"
            f"最近互动的基调是：{rel.recent_tone}。"
        )
    else:
        rel_text = f"说话的人是{speaker_id}，一个陌生人。"

    # 心情 + 精力 + 能量
    mood = state.runtime.derived_mood
    energy_text = f"她现在的精力水平是{state.runtime.energy:.1f}。" if state.runtime.energy < 0.5 else "她精力还行。"
    mood_text = f"她此刻的心情是{mood.label}。"

    # 场景
    scene_text = ""
    if state.scene:
        s = state.scene
        scene_text = (
            f"她正在{s.title}里。{s.description}。{s.atmosphere}。"
            f"{s.cognitive_narrative}"
        )

    # 决策指引（自然化）
    decision_text = (
        f"她此刻倾向于：{decision.response_mode.value.replace('_', ' ')}。"
    ) if decision.response_mode != ResponseDecision else "她自然地回应。"

    # 说话风格
    style_text = (
        f"她的说话风格是：{state.profile.speaking_style}。\n"
    )

    # 边界
    boundary_text = "\n".join([f"- {b}" for b in state.profile.boundaries])
    boundary_text = f"她的底线：\n{boundary_text}\n" if boundary_text else ""

    # 人设核心
    profile_text = (
        f"你是{state.profile.name}。{state.profile.background}\n"
        f"{state.profile.personality_summary}\n"
    )

    # 对话范例
    example_text = ""
    if state.profile.examples:
        example_lines = []
        for ex in state.profile.examples[:2]:
            example_lines.append(f"如果遇到：「{ex['situation']}」——她会说：「{ex['expected_reply']}」")
        example_text = "以下是她的对话风格范例：\n" + "\n".join(example_lines) + "\n\n"

    prompt = (
        f"{profile_text}\n"
        f"{style_text}\n"
        f"{example_text}"
        f"{boundary_text}\n"
        f"{scene_text}\n"
        f"{rel_text}\n"
        f"{energy_text} {mood_text}\n\n"
        + (f"她心里在意的事：\n" + "\n".join(concern_lines) + "\n\n" if concern_lines else "")
        + (f"她此刻想起来了：\n" + "\n".join(memory_lines) + "\n\n" if memory_lines else "")
        + f"{decision_text}\n\n"
        f"对方刚刚说：「{event.content}」\n\n"
        f"请用{state.profile.name}的口吻自然地回应。只输出她要说的话（一句或几句话），不要加任何前缀、标签或解释。"
    )

    return ExpressionContext(provider="deepseek", model=DEEPSEEK_MODEL, prompt=prompt)
