from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────

class ConcernStatus(str, Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    RESOLVED = "resolved"


class ResponseMode(str, Enum):
    WARM_REPLY = "warm_reply"
    NEUTRAL_REPLY = "neutral_reply"
    SHORT_AVOIDANCE = "short_avoidance"
    TOPIC_SHIFT = "topic_shift"
    QUESTION_BACK = "question_back"
    SILENCE = "silence"
    DELAYED_REPLY = "delayed_reply"
    EMOTIONAL_OUTBURST = "emotional_outburst"


class CognitiveModuleName(str, Enum):
    APPRAISAL = "appraisal"
    MEMORY_RETRIEVAL = "memory_retrieval"
    RESPONSE_DECISION = "response_decision"
    REPLY_GENERATION = "reply_generation"
    STATE_UPDATE = "state_update"


# ── Persona Profile ─────────────────────────────────────────────

class PersonalityFacet(BaseModel):
    label: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    tension: str = ""
    expression: str = ""


class CharacterProfile(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    background: str
    personality_traits: list[str] = Field(default_factory=list)
    personality_summary: str = ""
    personality_facets: list[PersonalityFacet] = Field(default_factory=list)
    speaking_style: str
    values: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)  # {"situation": ..., "expected_reply": ...}


# ── Concern ──────────────────────────────────────────────────────

class Concern(BaseModel):
    id: str
    title: str
    object: Optional[str] = None
    type: str = ""
    description: str
    intensity: float = Field(ge=0.0, le=1.0)
    valence: float = Field(ge=-1.0, le=1.0)
    arousal: float = Field(ge=0.0, le=1.0)
    triggers: list[str] = Field(default_factory=list)
    possible_resolutions: list[str] = Field(default_factory=list)
    last_activated_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    decay_rate: float = Field(ge=0.0, le=1.0, default=0.01)
    status: ConcernStatus = ConcernStatus.ACTIVE


# ── Relationship ─────────────────────────────────────────────────

class Relationship(BaseModel):
    target_id: str
    target_name: str
    familiarity: float = Field(ge=0.0, le=1.0, default=0.0)
    trust: float = Field(ge=0.0, le=1.0, default=0.0)
    affection: float = Field(ge=-1.0, le=1.0, default=0.0)
    tension: float = Field(ge=0.0, le=1.0, default=0.0)
    last_interaction_at: Optional[datetime] = None
    recent_tone: str = ""
    unresolved_issues: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


# ── Memory ───────────────────────────────────────────────────────

class ShortTermMemory(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker_id: str
    speaker_name: str
    content: str
    event_id: str


class LongTermMemory(BaseModel):
    id: str
    summary: str
    related_people: list[str] = Field(default_factory=list)
    related_concerns: list[str] = Field(default_factory=list)
    emotional_valence: float = Field(ge=-1.0, le=1.0, default=0.0)
    emotional_intensity: float = Field(ge=0.0, le=1.0, default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: Optional[datetime] = None
    importance: float = Field(ge=0.0, le=1.0, default=0.5)


# ── Runtime State ────────────────────────────────────────────────

class RuntimeSignalProfile(BaseModel):
    label: str
    summary: str
    considerations: list[str] = Field(default_factory=list)
    cognitive_narrative: str = ""


class DerivedMood(BaseModel):
    valence: float = Field(ge=-1.0, le=1.0, default=0.0)
    arousal: float = Field(ge=0.0, le=1.0, default=0.5)
    label: str = "neutral"


class RuntimeState(BaseModel):
    attention_focus: Optional[str] = None
    energy: float = Field(ge=0.0, le=1.0, default=0.7)
    derived_mood: DerivedMood = Field(default_factory=DerivedMood)
    signal_profiles: dict[str, RuntimeSignalProfile] = Field(default_factory=dict)
    active_concern_ids: list[str] = Field(default_factory=list)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)


# ── Scene ────────────────────────────────────────────────────────

class SceneState(BaseModel):
    id: str
    title: str
    description: str = ""
    atmosphere: str = ""
    visible_cues: list[str] = Field(default_factory=list)
    active_objects: list[str] = Field(default_factory=list)
    sensory_profile: str = ""
    interaction_pressure: str = ""
    cognitive_narrative: str = ""


# ── Character State (top-level aggregate) ───────────────────────

class CharacterState(BaseModel):
    profile: CharacterProfile
    concerns: list[Concern] = Field(default_factory=list)
    relationships: dict[str, Relationship] = Field(default_factory=dict)
    short_term_memory: list[ShortTermMemory] = Field(default_factory=list)
    medium_term_memory: list[ShortTermMemory] = Field(default_factory=list)
    long_term_memory: list[LongTermMemory] = Field(default_factory=list)
    runtime: RuntimeState = Field(default_factory=RuntimeState)
    scene: Optional[SceneState] = None


# ── Event ────────────────────────────────────────────────────────

class EventInput(BaseModel):
    id: str
    type: str = "user_message"  # user_message | system_tick | mention | room_event | internal_trigger
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    room_id: str = "main_room"
    content: str
    metadata: dict = Field(default_factory=dict)


# ── Pipeline Step Outputs ────────────────────────────────────────

class ActivatedConcern(BaseModel):
    concern_id: str
    activation_score: float = Field(ge=0.0, le=1.0)
    matched_triggers: list[str] = Field(default_factory=list)
    reason: str = ""


class AppraisalResult(BaseModel):
    event_id: str
    activated_concerns: list[ActivatedConcern] = Field(default_factory=list)
    event_salience: float = Field(ge=0.0, le=1.0, default=0.0)
    appraisal_summary: str = ""


class RecalledMemory(BaseModel):
    memory_id: str
    summary: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class MemoryRecallResult(BaseModel):
    short_term_context: list[ShortTermMemory] = Field(default_factory=list)
    long_term_memories: list[RecalledMemory] = Field(default_factory=list)


class ResponseDecision(BaseModel):
    should_respond: bool = True
    response_mode: ResponseMode = ResponseMode.NEUTRAL_REPLY
    delay_seconds: Optional[float] = None
    rationale: str = ""


class ConcernUpdate(BaseModel):
    concern_id: str
    intensity_delta: Optional[float] = None
    valence_delta: Optional[float] = None
    arousal_delta: Optional[float] = None
    status: Optional[ConcernStatus] = None
    note: str = ""


class RelationshipUpdate(BaseModel):
    target_id: str
    familiarity_delta: Optional[float] = None
    trust_delta: Optional[float] = None
    affection_delta: Optional[float] = None
    tension_delta: Optional[float] = None
    note: str = ""


class NewConcern(BaseModel):
    title: str
    description: str
    intensity: float = Field(ge=0.0, le=1.0)
    valence: float = Field(ge=-1.0, le=1.0)
    arousal: float = Field(ge=0.0, le=1.0)
    triggers: list[str] = Field(default_factory=list)


class StateUpdatePlan(BaseModel):
    concern_updates: list[ConcernUpdate] = Field(default_factory=list)
    relationship_updates: list[RelationshipUpdate] = Field(default_factory=list)
    new_concerns: list[NewConcern] = Field(default_factory=list)
    internal_state_note: str = ""


# ── Reply Output ─────────────────────────────────────────────────

class ReplyOutput(BaseModel):
    reply: str


# ── Cognitive Module Trace ───────────────────────────────────────

class CognitiveModuleRequest(BaseModel):
    module_name: CognitiveModuleName
    input_mode: str = "structured_context"  # natural_language | structured_context
    output_mode: str = "structured_json"    # natural_language | structured_json
    prompt: str  # 喂给 LLM 的完整 prompt
    output_contract: Optional[str] = None   # JSON Schema 等结构化约束


class CognitiveModuleTrace(BaseModel):
    module_name: CognitiveModuleName
    request: CognitiveModuleRequest
    output: dict  # 解析后的结构化输出
    raw_response: str = ""  # LLM 原始响应
    transport: str = "deepseek_api"


class ExpressionContext(BaseModel):
    """只给 Reply LLM 的自然语言上下文——不含 JSON/字段名/工程术语"""
    provider: str = "deepseek"
    model: str
    prompt: str


# ── State Delta ──────────────────────────────────────────────────

class StateDelta(BaseModel):
    concern_changes: list[str] = Field(default_factory=list)
    relationship_changes: list[str] = Field(default_factory=list)
    memory_writes: list[str] = Field(default_factory=list)
    runtime_changes: list[str] = Field(default_factory=list)


# ── Pipeline Trace ───────────────────────────────────────────────

class PipelineTrace(BaseModel):
    event: EventInput
    appraisal: CognitiveModuleTrace
    memory_recall: CognitiveModuleTrace
    decision: CognitiveModuleTrace
    expression_context: ExpressionContext
    reply_output: ReplyOutput
    state_update: CognitiveModuleTrace
    state_delta: StateDelta
