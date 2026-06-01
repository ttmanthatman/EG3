# 虚拟人的心流 (Virtual Human Flow)

一个 LLM 驱动的虚拟角色对话系统——重点是让虚拟角色"有灵魂"。

## 核心理念

LLM 不是虚拟人本身，它只是"语言模块"。真正的灵魂在：
- **Concerns（关切清单）**：她在乎什么
- **Relationships（关系档案）**：她跟每个人的关系
- **Memory（三层记忆）**：她记得什么、什么正在浮现
- **Async Life（异步生命）**：没人说话时她也在变化

## 技术栈

- 后端：Python + FastAPI + LangGraph
- 前端：React + Vercel AI SDK
- 数据：PostgreSQL + pgvector
- 部署：Docker Compose → VPS (3.xiaogushi.us)

## 文档

- `docs/DEVELOPMENT_METHOD.md` — 开发方法
- `docs/AI_NAMING_REGISTRY.md` — AI 用命名登记表
- `docs/SYSTEM_FLOW.md` — 系统流程与架构图
- `docs/RESEARCH_NOTES.md` — 调研笔记

## 当前阶段

Phase 0：文档和基础设施搭建完成，即将进入 Phase 1（静态角色 + 基础对话）。
