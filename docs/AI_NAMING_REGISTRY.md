# AI Naming Registry

本文档是给 AI 使用的命名与关系登记表，用来避免长期开发中的命名混乱。Maxiao 不需要逐项阅读。

## 命名约定

| 类型 | 规则 | 示例 |
| --- | --- | --- |
| 文档文件 | 英文大写蛇形或清晰短语 | `SYSTEM_FLOW.md` |
| Python 类 | PascalCase | `ConcernManager` |
| Python 函数 | snake_case，动词开头 | `run_appraisal()` |
| Python 变量 | snake_case，名词明确 | `active_concern_ids` |
| TypeScript 组件 | PascalCase | `ConversationPanel` |
| TypeScript 函数 | camelCase，动词开头 | `createSession` |
| TypeScript 变量 | camelCase，名词明确 | `activePersonaId` |
| API 路由 | kebab-case 或 REST 风格 | `/api/conversation-sessions` |
| 数据库表 | snake_case 复数 | `conversation_sessions` |
| 数据库字段 | snake_case | `created_at` |
| 环境变量 | UPPER_SNAKE_CASE | `DATABASE_URL` |

## 概念命名表

| 概念 | 标准名称 | 类型 | 说明 | 禁用/避免名称 |
| --- | --- | --- | --- | --- |
| 项目 | `virtual-human-flow` | project | 当前 MVP 的工程代号 | `test-app`, `demo` |
| 用户 | `user` | domain entity | 使用或配置虚拟人的真人 | `client` |
| 虚拟人 | `persona` | domain entity | 可被配置、对话、呈现的虚拟角色 | `bot`, `agent` |
| 对话会话 | `conversation_session` | domain concept | 一次连续交互过程 | `chat`, `talk` |
| 消息 | `message` | domain entity | 用户或 persona 的单条输入输出 | `contentItem` |
| 关切 | `concern` | domain entity | persona 稳定在意的事项，是情绪的来源之一 | `moodItem` |
| 关系档案 | `relationship` | domain entity | persona 对某个对象的独立关系状态 | `friendship` |
| 场景 | `scene` | domain entity | 当前对话发生的环境和氛围 | `background` |
| 事件 | `event` | domain entity | 统一包装的消息、定时触发或内部触发 | `trigger` |
| 中期记忆 | `medium_term_memory` | domain concept | 覆盖数百到数千条消息的中间记忆层 | - |
| 管线追踪 | `pipeline_trace` | runtime object | 一轮对话的完整中间结果 | `debugInfo` |
| 认知模块 | `cognitive_module` | pipeline concept | Appraisal / Memory / Decision / State Update 这类独立 LLM 判断模块 | - |
| 回复上下文 | `expression_context` | runtime object | 只交给 Reply LLM 的自然语言上下文 | `promptData` |
| Prompt 生成器 | `prompt_generator` | pipeline module | 把认知模块输出转换成自然语言回复上下文 | - |
| 状态更新计划 | `state_update_plan` | runtime object | State Update LLM 生成的结构化状态变化 | - |
| 性格特性 | `personality_facet` | domain object | 一个性格摘要背后的来源、张力和表达方式 | - |

## 模块登记表

| 模块 | 路径 | 责任 | 输入 | 输出 | 状态 |
| --- | --- | --- | --- | --- | --- |
| Core Types | `src/core/types.py` | 定义 concern, relationship, memory, event, trace 等类型 | 无 | Python 类型/Pydantic models | **待实现** |
| Seed State | `src/data/seed_state.py` | 提供首个 persona (林安) 的初始状态 | 无 | `CharacterState` | **待实现** |
| Appraisal | `src/pipeline/appraisal.py` | 判断事件触发了哪些 concern | Event, CharacterState | AppraisalResult | **待实现** |
| Memory Retrieval | `src/pipeline/memory_retrieval.py` | 通过 LLM 判断哪些记忆会浮现 | event, appraisal, state | MemoryRecallResult | **待实现** |
| Response Decision | `src/pipeline/response_decision.py` | 判断是否回应和回应姿态 | appraisal, recall, state | ResponseDecision | **待实现** |
| Prompt Generator | `src/pipeline/prompt_generator.py` | 将认知模块输出转成自然语言回复上下文 | event, state, appraisal, recall, decision | ExpressionContext | **待实现** |
| Reply LLM | `src/pipeline/reply_llm.py` | 调用 Reply LLM，只生成角色台词 | ExpressionContext | ReplyOutput | **待实现** |
| State Updater | `src/pipeline/state_updater.py` | 判断并写回状态和记忆变化 | state, event, reply, context | next_state, StateDelta | **待实现** |
| Pipeline Orchestrator | `src/pipeline/orchestrator.py` | LangGraph 编排整个同步响应路径 | content, state | next_state, trace | **待实现** |
| Memory Consolidator | `src/background/memory_consolidator.py` | 短期→中期→长期记忆摘要 | 短期记忆 | 中期/长期记忆 | **待实现（Phase 6）** |
| Concern Decay | `src/background/concern_decay.py` | 未触发的关切强度缓慢衰减 | concerns | 更新后的 concerns | **待实现（Phase 6）** |
| Internal Monologue | `src/background/internal_monologue.py` | persona 的内心活动 | 当前状态 | 新的长期记忆 | **待实现（Phase 6）** |
| Proactive Scheduler | `src/background/proactive_scheduler.py` | 决定 persona 何时主动开口 | 当前状态 | ProactiveTrigger | **待实现（Phase 6）** |
| FastAPI Server | `src/server/main.py` | Web 后端 API + WebSocket | HTTP/WS 请求 | JSON/流式响应 | **待实现** |
| React App | `src/ui/` | 三栏工作台 UI（状态 / 聊天 / trace） | 用户输入 | UI | **待实现** |

## 外部服务登记表

| 服务 | 标准名称 | 用途 | 权限/密钥位置 | 风险 |
| --- | --- | --- | --- | --- |
| GitHub | `github` | 代码远程同步和版本回溯 | 本机 GitHub CLI | - |
| VPS | `production_vps` | MVP 部署 | 不写入仓库 | 只允许操作 `3.xiaogushi.us` |
| LLM API | `llm_api` | 认知模块和回复生成 | 后端环境变量 `LLM_API_KEY` | 密钥不能出现在前端 |
