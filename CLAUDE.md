# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

智能旅游助手系统 — 基于 AI 技术的全栈旅游规划平台，提供个性化行程推荐和实时流式对话咨询服务。

## 要求

- 使用中文
- 善于使用你掌握的 skills
- 下载遇到网络问题时优先告诉我
- 编码前思考，简洁优先，精准修改，目标驱动执行

## 当前进度

| 阶段 | 状态 |
|------|------|
| 一～四：骨架 + AI 规划 + 流式对话 + RAG | ✅ |
| 五：用户系统（JWT/Spring Security/登录注册/H2 数据库） | ✅ |
| 六：优化（Redis 缓存/工具增强） | ❌ |

## 架构（三层）

```
Vue 3 + Vant UI (:5174)
       │ HTTP REST + SSE (Vite proxy → :8080)
       ▼
Java Spring Boot 3.2 (:8080)
  Controller → Service → AgentGateway → OkHttp → localhost:5000
  + Spring Security + JWT + JPA + H2
       │
       ▼
Python FastAPI Agent (:5000)
  BaseAgent (Tool Calling Loop) + RAG (ChromaDB) + Memory (in-memory sessions)
       │ OpenAI-compatible API
       ▼
DeepSeek / SiliconFlow
```

- **Java 是骨架/网关** — REST API、参数校验、SSE 透传、认证授权、数据持久化。绝不直接调用大模型。
- **Python Agent 是大脑** — AI 推理、Tool Calling、RAG 检索、会话记忆。
- **Vue H5 是展示层** — 移动端优先，Vant UI 4.x，hash 路由，`max-width: 480px` 桌面居中。

### 数据存储

| 数据 | 位置 | 说明 |
|------|------|------|
| 用户/对话/收藏 | H2 `data/traveldb.mv.db` | JPA 自动建表，对话 >3 天自动清理 |
| RAG 知识库 | ChromaDB `rag/chroma_db/` | spots 已导入 11 条，food/traffic/tips 空 |
| 登录 token | 浏览器 localStorage | JWT 7 天有效 |

## 构建与运行

> 启动顺序：Python Agent → Java 后端 → Vue 前端

```bash
# 0. 环境变量（Java 和 Python 都需要）
export DEEPSEEK_API_KEY="sk-xxxxxxxx"
export HF_HUB_OFFLINE=1  # 阻止 sentence-transformers 联网

# 1. Python Agent（必须先启动）
cd travel-agent-py
pip install -r requirements.txt
python server.py                    # :5000

# 2. Java 后端
cd travel-server-java
./mvnw clean package -DskipTests    # 编译
./mvnw spring-boot:run              # :8080

# 3. Vue 前端
cd travel-h5
npm install
npm run dev                         # :5174
```

**测试账号**：`demo / demo123`（`DataInitializer.java` 启动时自动创建）

## 现有 API 接口

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 否 | 注册 |
| POST | `/api/auth/login` | 否 | 登录，返回 JWT |
| POST | `/api/travel/recommend` | 是 | 非流式旅游规划 |
| POST | `/api/travel/recommend/stream` | 是 | 流式规划（SSE 进度） |
| POST | `/api/travel/chat` | 是 | SSE 流式对话 |
| GET | `/api/chat/sessions` | 是 | 对话历史列表 |
| GET | `/api/chat/sessions/{id}/messages` | 是 | 会话消息 |
| DELETE | `/api/chat/sessions/{id}` | 是 | 删除会话 |
| POST | `/api/favorites` | 是 | 添加收藏 |
| GET | `/api/favorites` | 是 | 收藏列表 |
| DELETE | `/api/favorites/{id}` | 是 | 删除收藏 |
| GET | `/health` | 否 | Python Agent 健康检查 |

## Java 后端关键文件

| 文件 | 职责 |
|------|------|
| `TravelServerApplication.java` | `@SpringBootApplication` + `@EnableScheduling` |
| `controller/TravelController.java` | 规划（流式/非流式）+ 对话 SSE，chat 方法自动存消息到 DB |
| `controller/AuthController.java` | 注册/登录，BCrypt 加密，返回 JWT |
| `controller/ChatHistoryController.java` | 历史会话查询/删除，按 userId 隔离 |
| `controller/FavoriteController.java` | 收藏 CRUD |
| `service/TravelService.java` | 调用 AgentGateway，JSON → VO 映射 |
| `gateway/AgentGateway.java` | OkHttp 调 Python Agent，支持 plan/chat/planStream |
| `security/SecurityConfig.java` | 放行 `/api/auth/**`，其余需 JWT 认证 |
| `security/JwtUtils.java` | JWT 生成/验证/提取 userId |
| `security/JwtAuthFilter.java` | 从 `Authorization: Bearer` 头提取 token |
| `entity/User.java` / `ChatMessage.java` / `Favorite.java` | JPA 实体 |
| `repository/` | Spring Data JPA 接口 |
| `config/DataInitializer.java` | `CommandLineRunner`，启动时创建 demo 用户 |
| `config/GlobalExceptionHandler.java` | 400/401/403/500 统一处理 |
| `task/ChatCleanupTask.java` | `@Scheduled` 每天凌晨 3 点清理 >3 天消息 |
| `utils/LLMUtils.java` | **备用代码**，未被引用 |
| `resources/application.yml` | H2 数据源 + JPA + JWT secret + Agent 地址 |

### 重要模式

- **userId 在线程池中传递**：`TravelController.chat()` 在 `chatExecutor.execute()` 之前取出 `userId`（`final Long userId = ...`），因为 `SecurityContext` 不会自动传递到子线程。
- **SseEmitter 超时**：180 秒，与 OkHttp read-timeout 一致。
- **线程池**：`Executors.newFixedThreadPool(10)`，不是 Cached。

## Python Agent 关键文件

| 文件 | 职责 |
|------|------|
| `server.py` | FastAPI 入口：`/agent/plan`、`/agent/plan/stream`、`/agent/chat`、`/health` |
| `agents/base_agent.py` | Tool Calling Loop（`run_tool_loop` + `run_tool_loop_stream`），含 `on_progress` 回调 |
| `agents/travel_agent.py` | 旅游规划 Agent：4 工具 + `plan_stream()` 生成器（线程+队列模式） |
| `agents/chat_agent.py` | 对话 Agent："小旅"，3 工具，RAG 增强 |
| `tools/travel_tools.py` | 5 工具 + 执行器 + 内置景点知识库（fallback） |
| `memory/session_memory.py` | 多租户会话管理（LRU 淘汰），`get_messages_for_llm` 默认过滤 tool 消息 |
| `rag/chroma_store.py` | ChromaDB 封装，`local_files_only=True` 防联网超时，embedder 加载失败则降级 |

### 关键修复记录

- **`_execute_tool`** 只对 `search_spot` 注入 `rag_store`，其他工具不接受此参数（否则 TypeError）
- **`set_travel_context`** 使用 `get_or_create_session` 而非 `sessions.get`，解决首次规划上下文丢失
- **`_call_llm`** 有 try/except 包装为 `RuntimeError`
- **JSON 提取** 正则改为 `r'```json\s*([\s\S]*?)```'` 灵活匹配空白

## Vue 前端关键文件

| 文件 | 职责 |
|------|------|
| `src/router/index.js` | Hash 路由 7 页面 + `beforeEach` 守卫（未登录→/login） |
| `src/App.vue` | `<transition>` 淡入淡出 + 底部 Tabbar（登录/注册/收藏/详情页隐藏） |
| `src/stores/auth.js` | JWT token + 用户信息，localStorage 持久化 |
| `src/stores/chat.js` | 消息列表、流式状态、sessionId |
| `src/utils/request.js` | Axios：JWT 注入 + 401 跳登录 |
| `src/views/Home.vue` | 城市联想搜索（~120 城）+ 流式进度遮罩 + 动态热门城市轮换 |
| `src/views/Chat.vue` | fetch() SSE 消费 + 收藏 + 历史面板 + 新建对话 + 快捷提问（分页轮换） |
| `src/views/Detail.vue` | 折叠行程 + 预算表 + 咨询 AI 按钮 |
| `src/views/Login.vue` | 登录 + 测试用户快捷填入 |
| `src/views/Register.vue` | 注册 |
| `src/views/Profile.vue` | 用户信息 + 收藏入口 + 退出登录 |
| `src/views/Favorites.vue` | 收藏列表 + 长文本展开/收起 |
| `src/components/ChatBubble.vue` | Markdown 渲染（marked）+ XSS 过滤 + AI 白底边框/用户蓝底靠右 |
| `src/styles/common.css` | `max-width: 480px` 居中 + 动画 keyframes |

### 前端关键模式

- **SSE 消费**：`fetch()` + `ReadableStream` + `while (!streamEnded)` 循环解析 `data:` 行
- **JWT 传递**：`request.js` 拦截器自动加 header，但 SSE 的 `fetch()` 需手动加 `Authorization: Bearer`
- **进度遮罩**：Home.vue 用 `van-overlay` + SSE 进度事件实时更新文字
- **AI 气泡**：`#fff` 白底 + `1px solid #ebedf0` 边框 + 微阴影，与页面 `#f5f5f5` 背景区分
- **用户气泡**：`#1989fa` 蓝底白字，`margin-right: -16px` 贴边
- **桌面居中**：所有 fixed 元素用 `left: 50%; transform: translateX(-50%); max-width: 480px`

## 错误处理

- Java：`GlobalExceptionHandler` 处理 validation(400) / auth(401/403) / generic(500)
- Python：JSON 提取失败返回 `{success: false, error: "...", rawResponse: "..."}`
- 前端：`request.js` 拦截器 toast + 401 跳登录；Chat SSE 有 AbortController 120s 超时

## 参考文件（本地保留，未上传 GitHub）

- `项目文档.md` — 完整技术规范（部分过时）
- `项目demo.md` — 页面功能需求
- `项目样式.md` — CSS 参考
- `agent-golden-bird.md` — 原始 6 周计划（Node/Flow 设计，与实现不同）
- `common.css` — 早期 CSS 子集（实际使用 `travel-h5/src/styles/common.css`）
