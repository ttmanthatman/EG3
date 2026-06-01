# Project Memory

## 项目定位
- 虚拟角色对话系统，核心是让 LLM 驱动的角色"有灵魂"
- 不是 chatbot，是认知架构（Concern + Relationship + Memory + Async Life）
- MVP 部署在 3.xiaogushi.us（VPS: 45.62.123.222）

## 关键架构决策
- LLM 只是"语言模块"，角色本体在外部状态中
- 情绪不要拍平成一个数字，用 concern + relationship 做核心状态
- 认知模块（Appraisal/Memory/Decision/State Update）和 Reply LLM 严格分离
- Reply LLM 只接收自然语言，不混入 JSON/字段名/工程术语
- 三层记忆（短期+中期+长期），中期层是关键差异化设计
- 沉默必须被显式建模为动作

## 开发规则
- Codex 项目（/Users/maxiao/Documents/虚拟人的心流-1/）仅参考，不修改
- 每次开发前读取前置文档（DEVELOPMENT_METHOD + NAMING_REGISTRY + SYSTEM_FLOW）
- 不懂就问，不猜测用户意图
- 每一步可回溯（Git commit + push）
