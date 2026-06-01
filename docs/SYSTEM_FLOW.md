# System Flow

本文档说明系统如何运作、数据如何流动、模块之间如何调用。它既给 Maxiao 看，也给 AI 后续开发使用。

## 当前阶段

**Phase 0：文档和基础设施搭建**

- 已建立开发方法（DEVELOPMENT_METHOD.md）
- 已完成 MVP 前调研（RESEARCH_NOTES.md）
- 已建立 AI 命名登记表（AI_NAMING_REGISTRY.md）
- 已连接 GitHub 仓库（ttmanthatman/EG3）
- 系统流程文档（本文档）

## 总体开发工作流

```mermaid
flowchart TD
    A[Maxiao 描述架构意图] --> B[Flow 读取前置文档]
    B --> C[Flow 检查 Git 状态]
    C --> D{架构是否清楚}
    D -- 否 --> E[提问或启用 grill-me]
    E --> A
    D -- 是 --> F[调研类似项目和经验]
    F --> G[更新命名登记表]
    G --> H[更新系统流程文档]
    H --> I[实现最小可验证变更]
    I --> J[本地验证]
    J --> K[Git 提交留底]
    K --> L[Push 到 GitHub]
    L --> M{是否需要部署}
    M -- 是 --> N[备份线上配置]
    N --> O[部署到 3.xiaogushi.us]
    O --> P[记录回滚方式]
    M -- 否 --> Q[等待下一步]
    P --> Q
```

## 文档和代码关系

```mermaid
flowchart LR
    DM[DEVELOPMENT_METHOD.md] --> WORK[每轮开发动作]
    NR[AI_NAMING_REGISTRY.md] --> WORK
    SF[SYSTEM_FLOW.md] --> WORK
    WORK --> CODE[代码和配置]
    CODE --> NR
    CODE --> SF
    CODE --> GIT[Git 提交]
    GIT --> GH[GitHub: ttmanthatman/EG3]
    GH --> VPS[3.xiaogushi.us 部署]
```

## 虚拟人认知架构全景（目标态）

```mermaid
flowchart TB
    subgraph 同步响应路径["⚡ 同步响应路径（用户等待）"]
        E[事件输入 Event] --> A[Appraisal 路由层<br/>判断事件触发关切]
        A --> M[Memory Recall 记忆召回<br/>短/中期/长期记忆 Top-K]
        M --> D[Response Decision 决策层<br/>要不要回？怎么回？]
        D --> P[Prompt Generator<br/>认知结果→自然语言上下文]
        P --> R[Reply LLM<br/>只生成角色台词]
        R --> S[State Update LLM<br/>判断状态变化]
        S --> W[确定性写回<br/>clamp/append/commit]
    end

    subgraph 异步生命路径["🌙 异步生命路径（后台持续运行）"]
        MC[Memory Consolidation<br/>短期→中期→长期摘要]
        CD[Concern Decay<br/>未触发关切缓慢衰减]
        IM[Internal Monologue<br/>内心活动/自言自语]
        PS[Proactive Scheduler<br/>何时主动开口]
    end

    subgraph 核心状态["💾 持续存在的核心状态"]
        CS[Concerns 关切清单<br/>对象/强度/触发词/衰减率]
        RS[Relationships 关系档案<br/>亲密度/信任/好感/紧张度]
        MB[Memory Bank 记忆库<br/>短期原文 + 中期连续性 + 长期摘要/向量]
        RT[Runtime State 运行状态<br/>energy/mood/焦点]
    end

    W --> CS
    W --> RS
    W --> MB
    W --> RT

    MC --> MB
    CD --> CS
    IM --> MB
    PS --> E

    CS -.-> A
    RS -.-> A
    MB -.-> M
    RT -.-> D
```

## 同步响应路径详图（一条消息的旅程）

```mermaid
flowchart TD
    U["👤 用户发送消息"] --> EVT["📦 包装为 Event<br/>id, type, speaker, content"]
    
    EVT --> APP["🧠 Appraisal LLM<br/>输入: Event + Active Concerns + Relationships<br/>输出: activatedConcerns[], eventSalience"]
    
    APP --> MEM["📖 Memory Recall LLM<br/>输入: Event + AppraisalResult + Short/Medium/Long-term<br/>输出: top-3~5 条记忆"]
    
    MEM --> DEC["🎯 Decision LLM<br/>输入: AppraisalResult + MemoryRecall + State<br/>输出: shouldRespond, responseMode, delaySeconds"]
    
    DEC --> GEN["✍️ Prompt Generator<br/>认知输出 → 纯自然语言上下文<br/>不含 JSON/字段名/工程术语"]
    
    GEN --> REP["💬 Reply LLM<br/>只生成角色台词（自然语言）<br/>输出: reply"]
    
    REP --> UPD["🔄 State Update LLM<br/>输入: State + Event + Reply + Context<br/>输出: concernUpdates, relationshipUpdates,<br/>newConcerns, internalStateNote"]
    
    UPD --> WRT["✅ 确定性写回<br/>clamp 数值范围 → 写入记忆<br/>→ 更新关系 → 更新关切"]
    
    WRT --> OUT["📤 发送回复到聊天室<br/>（可能延迟 delaySeconds）"]
    WRT --> TRC["📊 写入 Pipeline Trace<br/>每步输入输出完整记录"]
```

## 三层记忆架构（Nomi AI 启发）

```mermaid
flowchart LR
    subgraph 记忆写入
        EVENT[新事件/回复]
    end
    
    subgraph 短期记忆
        STM["💭 Short-term<br/>最近 10-20 轮原文<br/>当前会话上下文"]
    end
    
    subgraph 中期记忆
        MTM["📝 Medium-term<br/>数百到数千条消息<br/>保持对话连续性<br/>含情感语气和时间感"]
    end
    
    subgraph 长期记忆
        LTM["🗄️ Long-term<br/>向量化永久存储<br/>重要性 × 情绪强度 × 时间衰减"]
    end
    
    EVENT --> STM
    STM -->|"定期压缩（每 20 条或按时触发）"| MTM
    MTM -->|"深度摘要 + 向量化"| LTM
    
    STM -->|"召回（必入）"| RETRIEVAL[记忆召回]
    MTM -->|"召回（相关 + 时间加权）"| RETRIEVAL
    LTM -->|"召回（Top-K）"| RETRIEVAL
```

## 当前 MVP UI 结构

```mermaid
flowchart LR
    LEFT["📋 左侧 State Panel<br/>Persona 档案<br/>Concerns 列表<br/>Relationships<br/>Runtime Signals<br/>Scene"] 
    
    CHAT["💬 中间 Chat Panel<br/>消息列表<br/>输入框<br/>回复（可能延迟/流式）"]
    
    RIGHT["🔍 右侧 Pipeline Trace<br/>Event<br/>Appraisal 输入/输出<br/>Memory Recall 输入/输出<br/>Decision 输入/输出<br/>Reply Prompt<br/>Reply Output<br/>State Update 输入/输出<br/>State Delta"]
```

## 当前模块状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 开发方法 | ✅ initialized | `docs/DEVELOPMENT_METHOD.md` |
| 命名登记 | ✅ initialized | `docs/AI_NAMING_REGISTRY.md` |
| 系统流程 | ✅ initialized | 本文档 |
| 调研笔记 | ✅ initialized | `docs/RESEARCH_NOTES.md` |
| 错误勘验 | ⏳ pending | 尚未发生需要勘验的错误 |
| Git 仓库 | ✅ initialized | 已连接 `ttmanthatman/EG3` |
| Phase 1: 静态角色 + 基础对话 | ⏳ pending | 待实现 |
| Phase 2: Concern 系统 | ⏳ pending | 待实现 |
| Phase 3: Relationship 系统 | ⏳ pending | 待实现 |
| Phase 4: 长期记忆召回 | ⏳ pending | 待实现 |
| Phase 5: 响应决策层 | ⏳ pending | 待实现 |
| Phase 6: 异步后台 | ⏳ pending | 待实现 |
| VPS 部署 | ⏳ pending | 待 Code + Docker配置完成后部署 |
