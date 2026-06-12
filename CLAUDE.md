# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

智能旅游助手系统 — 基于 AI 技术的旅游规划平台，提供个性化行程推荐和实时流式对话咨询服务。

## 要求
使用中文

善于使用你掌握的skills

下载遇到网络问题时优先告诉我

## 当前进度

| 阶段 | 状态 |
|---|---|
| 一～四：骨架 + AI 规划 + 流式对话 + RAG | ✅ 已完成 |
| 五：用户系统（JWT/Spring Security/登录注册） | ❌ 未开始 |
| 六：优化（Redis 缓存/工具增强/错误处理） | ❌ 未开始 |

> **注意**：当前无数据库（无 JPA/JDBC 依赖），无用户认证，无路由守卫。`LLMUtils.java` 是备用代码，**活动代码路径不经过它**。

## 架构（三层）

```
Vue 3 + Vant UI (:5174)
       │ HTTP REST + SSE (Vite proxy → :8080)
       ▼
Java Spring Boot 3.2 (:8080)
  Controller → Service → AgentGateway → OkHttp → localhost:5000
       │
       ▼
Python FastAPI Agent (:5000)
  BaseAgent (Tool Calling Loop) + RAG (ChromaDB) + Memory (in-memory sessions)
       │ OpenAI-compatible API
       ▼
DeepSeek / SiliconFlow
```

- **Java 是骨架/网关** — REST API、参数校验、SSE 透传。绝不直接调用大模型。
- **Python Agent 是大脑** — AI 推理、Tool Calling、RAG 检索、会话记忆。
- **Vue H5 是展示层** — 移动端优先，Vant UI 4.x，hash 路由。

### 请求实际流转路径

```
前端 POST /api/travel/recommend
  → TravelController.recommend()
    → TravelService.getTravelRecommend()
      → AgentGateway.plan(city, budget, days)   // OkHttp → Python :5000/agent/plan
        → TravelAgent.plan()
          → RAG 检索 → BaseAgent.run_tool_loop() → LLM → 工具调用循环
          → _parse_and_validate() 提取/校验 JSON
      ← JsonNode (结构化行程)
    ← TravelRecommendVO
  ← Result<TravelRecommendVO>

前端 POST /api/travel/chat (SSE)
  → TravelController.chat() → SseEmitter
    → 线程池中消费 AgentGateway.chat() 返回的 SSE 行
      → 每行解析为 StreamChunkVO/StreamDoneVO/StreamErrorVO 发送给前端
```

## 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 前端 | Vue 3 + Composition API、Vant UI、Pinia、Vue Router、Axios、Vite | Vue 3.4、Vant 4.9、Vite 5 |
| 主后端 | Spring Boot、OkHttp、Jackson、Lombok | SB 3.2.5、Java 17、OkHttp 4.12 |
| AI 引擎 | FastAPI、OpenAI SDK、ChromaDB、sentence-transformers | Python 3.x |
| 大模型 | DeepSeek（默认）/ SiliconFlow | 通过环境变量切换 |

## 关键设计决策（代码中已体现的）

1. **Java 不直接调 LLM** — `TravelService` → `AgentGateway` → `localhost:5000`。`LLMUtils` 存在但未被引用，仅作备用。
2. **SSE 透传模式** — Python Agent 推送 SSE 流，Java `AgentGateway.chat()` 逐行解析 `data:` 行，提取 `content` 后通过 `SseEmitter` 转发前端。对话在 `CachedThreadPool` 中运行，不阻塞主线程。
3. **JSON 提取降级链** — 大模型返回的 JSON 按 ` ```json ``` ` → ` ``` ``` ` → 最外层 `{...}` 优先级提取。Java（`TravelService`）和 Python（`TravelAgent._parse_and_validate`）各自实现。
4. **Python Agent 使用 Tool Calling Loop**（不是原来的 Node/Flow 设计）— `BaseAgent.run_tool_loop()` 是核心：发送 messages + tools → LLM 返回 `tool_calls` → 执行工具 → 追加结果 → 继续循环，最多 `max_tool_rounds` 轮。
5. **Vant 全局手动注册**（不是 auto-import）— `main.js` 中手动注册 17 个 Vant 组件。`@vant/auto-import-resolver` 已安装但**未启用**（4.9.x 兼容性问题）。
6. **Vant UI 锁定 v4.x** — 未经迁移计划不得升至 Vant 5。

## 构建与运行

> 启动顺序：Python Agent → Java 后端 → Vue 前端

```bash
# 1. Python Agent（必须先启动）
cd travel-agent-py
pip install -r requirements.txt
python server.py                    # :5000，需设 DEEPSEEK_API_KEY 或 SILICONFLOW_API_KEY 环境变量

# 2. Java 后端
cd travel-server-java
mvn clean install
mvn spring-boot:run                 # :8080，LLM 密钥通过环境变量注入

# 3. Vue 前端
cd travel-h5
npm install
npm run dev                         # :5174，Vite proxy 将 /api → :8080
```

**LLM 密钥环境变量**：`DEEPSEEK_API_KEY` 或 `SILICONFLOW_API_KEY`（Java 和 Python 都需要，各读各的配置）。

## Java 后端关键文件

| 文件 | 职责 |
|---|---|
| `TravelServerApplication.java` | Spring Boot 入口 |
| `controller/TravelController.java` | `POST /api/travel/recommend`（非流式）+ `POST /api/travel/chat`（SSE） |
| `service/TravelService.java` | 调用 `AgentGateway.plan()`，将 JSON 映射为 `TravelRecommendVO` |
| `gateway/AgentGateway.java` | OkHttp 与 Python Agent 通信：`plan()` 同步、`chat()` 流式解析 SSE 行 |
| `config/CorsConfig.java` | 全局 CORS 放行 |
| `config/GlobalExceptionHandler.java` | 参数校验异常 → 400，兜底 → 500 |
| `dto/TravelRequestDTO.java` | city（`@NotBlank`）、budget（`@Min(100)`）、days（`@Min(1) @Max(30)`） |
| `dto/ChatRequestDTO.java` | message（`@NotBlank`） |
| `vo/Result.java` | 统一响应 `{code, message, data}`，静态工厂 `ok()`/`fail()` |
| `vo/TravelRecommendVO.java` | 行程响应，含内嵌类 `DailyItinerary`、`TimeSlot`、`BudgetBreakdown` |
| `vo/StreamChunkVO.java` / `StreamDoneVO.java` / `StreamErrorVO.java` | SSE 事件类型 |
| `utils/LLMUtils.java` | **备用**：直接调 LLM API（非流式 + 流式 + JSON 提取）。当前未被使用 |
| `resources/application.yml` | 服务器端口、LLM 提供商切换、Agent 地址、日志级别 |

## Python Agent 关键文件

| 文件 | 职责 |
|---|---|
| `server.py` | FastAPI 入口：`/agent/plan`、`/agent/chat`（SSE）、`/health`、`/agent/history/{id}`、`/agent/stats` |
| `agents/base_agent.py` | `BaseAgent` 抽象类：Tool Calling Loop（`run_tool_loop` + `run_tool_loop_stream`） |
| `agents/travel_agent.py` | `TravelAgent(BaseAgent)`：旅游规划，4 个工具，JSON 提取校验 |
| `agents/chat_agent.py` | `ChatAgent(BaseAgent)`："小旅"对话助手，3 个工具，流式输出 |
| `tools/travel_tools.py` | 5 个工具定义 + 执行器：`search_spot`、`check_ticket`、`calc_budget`、`search_web`、`travel_plan_done` |
| `memory/session_memory.py` | `MemoryManager`：多租户会话（最多 1000 个，LRU 淘汰），`Session` 含消息历史和旅行上下文 |
| `rag/chroma_store.py` | `TravelRAGStore`：ChromaDB 4 个 Collection（`spots`/`food`/`traffic`/`tips`），sentence-transformers 嵌入 |
| `rag/importer.py` | Markdown → ChromaDB 导入脚本（`python importer.py`） |
| `rag/knowledge/spots.md` | 景点知识库（北京/杭州/成都/西安/上海，约 10 个景点） |

### Tool Calling Loop 流程

```
用户消息 → 获取/创建 Session → 组装 messages（system + context + history + user）
  → 带 tools 调 LLM
    → finish_reason == "tool_calls" → 执行工具 → 追加 assistant/tool messages → 继续循环
    → 有文本内容 → 存入 Memory → 返回（流式版逐 3 字符 yield）
  → 超 max_tool_rounds → 返回超时消息
```

### RAG 状态

| Collection | 数据 |
|---|---|
| `spots` | ✅ 已导入（5 个城市的 10 个景点） |
| `food` | ❌ 空 |
| `traffic` | ❌ 空 |
| `tips` | ❌ 空 |

## Vue 前端关键文件

| 文件 | 职责 |
|---|---|
| `vite.config.js` | 端口 5174，`/api` proxy → `localhost:8080` |
| `src/main.js` | 全局注册 17 个 Vant 组件 + Vant CSS + Pinia + Router |
| `src/router/index.js` | Hash 路由，4 个懒加载页面，无路由守卫 |
| `src/App.vue` | `router-view` + 底部 Tabbar（首页/对话/我的），`/detail` 页隐藏 Tabbar |
| `src/stores/chat.js` | Pinia store：消息列表、流式状态、用户头像/昵称、收藏夹（localStorage 持久化） |
| `src/utils/request.js` | Axios 实例：`baseURL: /api`，120s 超时，响应拦截器解包 `Result` |
| `src/views/Home.vue` | 城市 Picker（38 城）+ 预算/天数 Field + 热门城市卡片（8 个）→ POST → sessionStorage → 跳转 |
| `src/views/Detail.vue` | 读 sessionStorage → 折叠面板每日行程 + BudgetTable + 提示/注意事项 + "咨询 AI"按钮 |
| `src/views/Chat.vue` | **用 fetch() 读 SSE 流**（非 Axios）→ 拼接到最后一条 AI 消息 → 打字机效果。空态显示 4 个快捷问题 |
| `src/views/Profile.vue` | 头像/昵称编辑（同步 chatStore）+ 服务菜单（均"功能开发中"）+ 关于弹窗 |

### 前端流式实现要点

Chat.vue 的 SSE 消费方式：
```js
const response = await fetch('/api/travel/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message })
})
const reader = response.body.getReader()
const decoder = new TextDecoder()
// 逐行读取，解析 "data: {...}" 行，根据 type 分发
```

### 页面间数据传递

- **Home → Detail**：`sessionStorage.setItem('travelPlan', JSON.stringify(responseData))`
- **Detail → Chat**：`sessionStorage.setItem('chatContext', '去${city}玩${days}天，有什么推荐和注意事项？')`，Chat 页 mount 时检测并自动发送后清除

## 参考文件

| 文件 | 说明 |
|---|---|
| [项目文档.md](项目文档.md) | 完整技术规范（API 合约、数据模型、提示词、实体定义），部分内容已过时（如 LangChain 引用） |
| [agent-golden-bird.md](agent-golden-bird.md) | 6 周实施方案，Node/Flow 设计与实际实现不同 |
| [项目demo.md](项目demo.md) | 四页面功能需求和交互细节 |
| [项目样式.md](项目样式.md) | Detail 和 Chat 页 CSS 参考 |
| [common.css](common.css) | 公共 CSS 工具类（已是前端 `src/styles/common.css` 的子集） |
| [组件部分源码/](组件部分源码/) | 3 个组件的参考模板（与 `travel-h5/src/components/` 内容一致） |

## 核心数据模型

```
TravelRecommendVO
├── success: Boolean
├── city: String
├── days: Integer
├── totalBudget: Integer
├── dailyItinerary: List<DailyItinerary>
│   ├── day: Integer, date: String
│   ├── morning / afternoon / evening: TimeSlot
│   │   └── spot, duration, ticket, transportation, description (均为 String)
├── budgetBreakdown: BudgetBreakdown
│   └── accommodation, food, transportation, tickets, other (均为 Integer)
├── tips: List<String>
├── warnings: List<String>
├── error: String
└── rawResponse: String
```

> 注意：Java VO 中 `budgetBreakdown` 字段名为 `tickets`（复数），前端 `BudgetTable.vue` 也读取 `tickets`。

## 现有 API 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/travel/recommend` | 非流式旅游规划，返回 `Result<TravelRecommendVO>` |
| POST | `/api/travel/chat` | SSE 流式对话，请求 `{message}`，返回 chunk/done/error 事件 |
| POST | `/agent/plan` | Python 内部：规划接口 |
| POST | `/agent/chat` | Python 内部：SSE 对话接口 |
| GET | `/health` | Python 健康检查 + RAG 统计 |
| GET | `/agent/history/{session_id}` | Python 内部：会话历史 |
| GET | `/agent/stats` | Python 内部：全局统计 |

## 错误处理模式

- **参数校验**：`GlobalExceptionHandler` 捕获 `MethodArgumentNotValidException` → `Result.fail(400, 聚合消息)`
- **JSON 解析失败**：`TravelService.parseAgentResponse()` 设 `success=false` + `error` 字段 + `rawResponse`，不抛异常
- **流式解析失败**：`AgentGateway` 跳过无法解析的 SSE 行，不中断流
- **Python Agent 异常**：`TravelAgent._parse_and_validate()` 返回 `{success: false, error: ..., rawResponse: ...}`
- **前端网络错误**：`request.js` 拦截器 toast 错误信息；Chat 页 fetch 异常直接显示

## 规范

### 1. 编码前思考
明确说明假设 — 如果不确定，询问而不是猜测。呈现多种解释 — 当存在歧义时，不要默默选择。适时提出异议 — 如果存在更简单的方法，说出来。

### 2. 简洁优先
用最少的代码解决问题。不要为一次性代码创建抽象，不要添加未要求的"可配置性"，不要为不可能发生的场景做错误处理。

### 3. 精准修改
只碰必须碰的。不要"改进"相邻代码/注释/格式，不要重构没坏的东西。匹配现有风格（手动 getter/setter、中文注释、`<script setup>`）。
当你注意到无关的死代码时，提一下但不要删除。

### 4. 目标驱动执行
将指令式任务转化为可验证的目标。对于多步骤任务，说明简短计划：
```
1. [步骤] → 验证: [检查]
2. [步骤] → 验证: [检查]
```
