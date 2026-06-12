# AI 旅游规划平台 — 实施方案

## Context

用户刚学完了 Python Agent 开发全流程（Node/Flow/Tools/Memory/RAG/Goal），手上有一份 Java 版旅游推荐系统的参考文档。现在要做一个完整的网页版旅游平台，Java 做主后端，Python 做 AI Agent 引擎，Vue 做前端。

## 架构总览

```
Vue 3 + Vant UI (前端)
       │ HTTP REST + SSE
       ▼
Java Spring Boot 3.2 (:8080)
  主后端：用户系统、API网关、数据持久化、鉴权
       │ HTTP (内网 localhost:5000)
       ▼
Python Agent 服务 (:5000, FastAPI)
  AI 大脑：旅游规划Agent、对话Agent、RAG检索
  复用 Learn-OpenClaw 的 core/ 和 tools/
```

**原则**：Java 是骨架（用户、鉴权、数据库、API），Python Agent 是大脑（AI推理、工具调用、RAG）。

## 技术选型

| 层 | 技术 | 说明 |
|---|------|------|
| 前端 | Vue 3 + Vant UI 4 + Vite | 复用参考项目的 ChatBubble/SpotItem/BudgetTable 组件 |
| 主后端 | Spring Boot 3.2 + Java 17 + Maven | 参考项目文档中的接口设计 |
| AI引擎 | Python FastAPI + Learn-OpenClaw Agent 框架 | 复用 core/node.py、core/llm.py、tools/ |
| RAG | ChromaDB | 景点/美食/交通/贴士 4 个 Collection |
| 数据库 | MySQL (用户、行程历史) + Redis (Session缓存) | |
| 通信 | Java ↔ Python: HTTP JSON + SSE 流式 | |

## API 设计

### Java 后端暴露给前端
- `POST /api/travel/recommend` — 非流式，返回结构化行程 JSON
- `POST /api/travel/chat` — SSE 流式对话
- `POST /api/user/register` / `POST /api/user/login` — 用户系统
- `GET /api/travel/history` — 历史规划列表

### Python Agent 暴露给 Java
- `POST /agent/plan` — 接收 {city, budget, days, user_preferences} → 返回完整行程 JSON
- `POST /agent/chat` — SSE 流式对话，含工具调用状态通知
- `GET /health` — 健康检查

## Python Agent 核心设计

### 旅游规划 Agent Flow
```
RAGRetrieveNode → PlanBuildNode → TravelLLMNode ⇄ ToolNode → ValidateNode
   (检索知识库)    (组装提示词)     (调LLM+tools)   (执行工具)   (校验JSON)
```

### 自定义旅游工具（复用 Tool 类）
- `search_spot` — 搜索真实景点信息（先查RAG再上网）
- `search_web` — DuckDuckGo 搜索最新攻略
- `check_ticket` — 查询景点门票价格
- `calc_budget` — 核算预算分配
- `travel_plan_done` — 标记规划完成（类似 goal_complete）

### 对话 Agent Flow
```
ChatNode ⇄ ToolNode (回路模式，复用 agent_demo.py 结构)
```

### RAG 知识库
```
ChromaDB Collections:
  spots/ — 景点攻略
  food/ — 美食推荐
  traffic/ — 交通指南
  tips/ — 旅行贴士
```
数据：手动整理 10-15 个热门城市的结构化文档，批量导入。

## 开发阶段（6 周）

### 第一阶段：骨架搭建
1. Python Agent 基础服务 — FastAPI + 引入 core/tools
2. Java 后端骨架 — Controller/Service/Gateway + mock 数据
3. Vue 前端骨架 — 4 页面路由 + Axios + Vant UI

### 第二阶段：AI 旅游规划
4. Python 旅游规划 Flow — 全部 Node + Tool + 系统提示词
5. Java 对接 Python — AgentGateway 非流式调用 + JSON 解析
6. Vue 规划功能 — Home 表单 → Detail 行程展示

### 第三阶段：AI 对话 + 流式
7. Python 对话 Agent + SSE 端点
8. Java SSE 透传到前端
9. Vue Chat 页面 — 流式打字机效果

### 第四阶段：RAG 知识库
10. 整理城市知识文档
11. ChromaDB 入库 + 检索封装
12. RAG 增强规划和对话

### 第五阶段：用户系统
13. Java 用户系统 — JWT 认证 + Spring Security
14. 行程历史持久化
15. Vue 登录注册 + 路由守卫

### 第六阶段：优化完善
16. Memory 多租户会话管理
17. 工具增强（calc_budget/check_ticket 真实实现）
18. 性能优化（Redis 缓存）、错误处理

## 关键文件

**复用（不改动）**：
- `Learn-OpenClaw-main/core/node.py` — Node/Flow 基类
- `Learn-OpenClaw-main/tools/builtins/tool_def.py` — Tool 类
- `Learn-OpenClaw-main/tools/builtins/search.py` — DuckDuckGo 搜索

**新建 Python Agent**：
- `travel-agent-py/server.py` — FastAPI 入口
- `travel-agent-py/agents/travel_agent.py` — 旅游规划 Flow
- `travel-agent-py/agents/chat_agent.py` — 对话 Agent
- `travel-agent-py/tools/travel_tools.py` — 旅游专属工具
- `travel-agent-py/rag/chroma_store.py` — ChromaDB 封装
- `travel-agent-py/rag/importer.py` — 知识导入脚本

**新建 Java**：参考项目文档的包结构，实现 Controller/Service/Gateway

**新建 Vue**：复用参考项目的 ChatBubble/SpotItem/BudgetTable 组件

## 验证方式

1. Python Agent 单测：用 curl 调 `/agent/plan` 验证 JSON 输出
2. Java 集成测试：用 Apifox 调 `/api/travel/recommend` 端到端
3. 前端 E2E：首页填表 → 看到 AI 生成行程 → 进入对话 → 流式回复
4. RAG 验证：对比有无 RAG 的规划精度差异
