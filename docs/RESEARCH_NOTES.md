# Research Notes

本文档记录动手前的相近项目、原理和踩坑。后续每次引入新架构或新技术时继续追加。

## 2026-06-01 MVP 前调研（Flow 独立调研 + 借鉴 Codex 成果）

### 一、Codex（GPT-5.5）已覆盖的方向

以下方向 Codex 已在 `/Users/maxiao/Documents/虚拟人的心流-1/docs/RESEARCH_NOTES.md` 中充分调研，此处仅记录结论：

| 方向 | 来源 | 对本项目的启发 |
|------|------|-------------|
| Generative Agents | arXiv: 2304.03442 | 可信虚拟行为 = observation + memory + reflection + planning；先把外部状态和记忆召回做成可观察 pipeline |
| MemGPT / Letta | arXiv: 2310.08560 | 长对话需要分层记忆和上下文管理；MVP 先区分短期原文和长期摘要 |
| OCC / Appraisal 情绪模型 | PMC: PMC4243519 | 情绪是事件×情境的评估结果，不是全局数字；用 concern + relationship 做核心状态 |
| ReAct | arXiv: 2210.03629 | 推理和行动交替有助于可解释性；逐步展示每个 LLM 模块的输入/输出 |
| OpenAI Structured Outputs | platform.openai.com | 认知模块使用 JSON Schema，Reply LLM 不使用结构化约束 |

### 二、Flow 补充的海外调研（Codex 未覆盖）

#### 2.1 Nomi AI：三层记忆系统的工业级实践

- **来源**：https://www.aicompanionpick.com/character-ai-vs-replika-vs-nomi-memory-comparison
- **核心发现**：Nomi 是当前消费级 AI 伴侣中记忆最强的（评分 9/10），关键在于**中期记忆层**——覆盖 1,000+ 条消息前的对话，包括具体内容、笑话、情感语气。这是其他平台"记忆断崖"的根因。
- **对本项目的启发**：
  - 短期记忆（当前会话）+ 中期记忆（数周前的对话连续性）+ 长期记忆（向量化永久存储）——三层而非两层
  - 存储体验而非只存储事实：信息 + 语境 + 情感色彩 + 时间感一起保留
  - Identity Core 锚定人格特征，防止跨会话人格漂移
  - **中期记忆层是我们当前设计的核心缺失**

#### 2.2 OpenHer：人格从神经驱动中涌现

- **来源**：https://github.com/kellyvv/OpenHer
- **核心发现**："Personality emerges from neural drives, not prompts." 人格不应该被 prompt 硬编码，而应该像人一样从底层驱动力中自然涌现。
- **对本项目的启发**：Concern 不应该只是"被激活的标签"，而应该像真正的心理驱动力一样有"推力"。这是 Concern 架构的进阶方向，MVP 阶段可暂不实现，但设计上预留空间。

#### 2.3 Alice：压力场引擎（Pressure Field Engine）

- **来源**：https://github.com/LlmKira/Alice
- **核心发现**：用"压力场"模拟内在动机——类似于生物的需求-行为驱动模型。不是被动等事件触发，而是从内部产生行为驱动力。
- **对本项目的启发**：压力场可以作为 Proactive Scheduler（异步生命路径中的主动性调度）的理论基础。MVP 阶段可用简化版调度器，但架构上应预留"内在驱动力"与"外部事件"两条触发路径。

#### 2.4 LangGraph：认知 Pipeline 的最佳底层编排框架

- **来源**：https://github.com/langchain-ai/langgraph
- **核心发现**：LangGraph 是专为 stateful, long-running agents 设计的低级编排框架。核心概念——有向图、条件分支、循环、状态持久化——天然适合我们的认知 Pipeline。
- **对本项目的启发**：用 LangGraph 替代手写 TypeScript 管线，可以获得：
  - 状态持久化和断点续跑（调试时极其重要）
  - 条件分支（根据 appraisal 结果决定是否跳过某些步骤）
  - 循环（自言自语模块可能触发新的 appraisal）
  - 内置的 tracing 和 observability

#### 2.5 Vercel AI SDK：Web UI 的建楼地基

- **来源**：https://sdk.vercel.ai/docs
- **核心发现**：Provider-agnostic TypeScript 工具包，支持 streaming、tool calling、structured output。不绑死任何 LLM 供应商。
- **对本项目的启发**：
  - 解决"真实 LLM 接入"问题——不需要手写 mock adapter
  - 流式 UI 开箱即用——角色回复可以逐字出现而非一次性显示
  - 可以用 `useChat` hook 快速搭建聊天 UI

#### 2.6 其他值得关注的开源项目

| 项目 | 星标 | 与本项目相关的亮点 |
|------|------|------------------|
| memobase (memodb-io) | 2.7k | 基于用户画像的长时记忆系统，可作为长期记忆存储层的参考实现 |
| powermem (OceanBase) | 687 | 企业级 AI 记忆插件，上下文工程能力强 |
| CyberVerse (dsd2077) | 1.1k | Persona Memory 作为一级功能，WebRTC 实时语音 |

### 三、当前落地取舍

| 方向 | 当前选择 | 原因 |
|------|---------|------|
| 技术栈 | Python (FastAPI + LangGraph) 后端 + React (Vercel AI SDK) 前端 | 能力优先：Python 在 LLM 生态绝对领先；React 在 Web UI 生态最成熟 |
| 记忆 | 短期原文 + 中期连续性 + 长期摘要/向量 | Nomi AI 实践证明三层记忆是"活感"的关键 |
| 情绪 | concern + relationship + derivedMood | 避免把心理状态压成一个数字 |
| 认知 Pipeline | LangGraph 编排 | 比手写管线更结构化，支持持久化和断点调试 |
| 主动性 | MVP 先做简化调度器，预留压力场接口 | 异步生命路径是"活感"来源，但 MVP 先跑通同步路径 |
| LLM | 前端 Vercel AI SDK 直连 + 后端代理 | 结构化输出走认知模块（JSON Schema），回复走自然语言 |
| UI | React 三栏工作台 | 用户需要直观看到状态、聊天和 pipeline trace |

### 四、下一步需要确认的技术决策

1. LLM 供应商：用 DeepSeek API / OpenAI API / 还是本地部署？
2. 是否需要 Voice（语音）功能？如果需要，WebRTC 还是简单 TTS？
3. MVP 的"最小可验证闭环"具体是什么？——是单条消息走完 Pipeline 还是有其他验收标准？
