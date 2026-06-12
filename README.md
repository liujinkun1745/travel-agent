# 🧳 智能旅游助手

AI 驱动的全栈旅游规划平台 — 个性化行程推荐 + 实时流式对话 + RAG 知识增强 + 用户系统。

![Vue](https://img.shields.io/badge/Vue-3.4-42b883?logo=vue.js)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2-6db33f?logo=spring)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?logo=fastapi)
![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek-536dfe)
![H2](https://img.shields.io/badge/DB-H2-0072b8)

---

## ✨ 功能

- 🤖 **AI 智能规划** — 输入目的地/预算/天数，Agent 调用工具查询景点、门票、预算，生成完整行程
- 📡 **流式进度反馈** — 规划过程实时 SSE 推送进度（检索 → 查景点 → 算预算 → 生成）
- 💬 **流式对话** — SSE 实时打字机效果，多轮对话带记忆，Markdown 渲染
- 👤 **用户系统** — JWT 认证、注册登录、路由守卫，用户间数据隔离
- 📚 **RAG 知识库** — ChromaDB + sentence-transformers 本地向量检索
- 📝 **对话历史** — H2 持久化存储，自动清理 3 天前记录
- ⭐ **收藏** — 收藏 AI 回答，永久保存
- 🔍 **城市联想搜索** — 支持 120+ 城市自由输入 + 下拉联想
- 🎨 **响应式设计** — 移动端优先，桌面端 480px 居中

---

## 🏗 架构

```
Vue 3 + Vant UI (:5174)
       │ HTTP REST + SSE + JWT (Vite proxy → :8080)
       ▼
Java Spring Boot 3.2 (:8080) — 网关 + 认证 + 数据持久化
  Controller → Service → AgentGateway → OkHttp → localhost:5000
  Spring Security + JWT + JPA + H2
       │
       ▼
Python FastAPI Agent (:5000) — AI 大脑
  Tool Calling Loop + RAG (ChromaDB) + Session Memory
       │ OpenAI API
       ▼
  DeepSeek LLM
```

---

## 🚀 快速开始

### 环境

| 依赖 | 版本 |
|------|------|
| Node.js | ≥18 |
| Java | ≥17 |
| Python | ≥3.10 |

### 启动

```bash
# 0. 设置 LLM 密钥
export DEEPSEEK_API_KEY="sk-xxxxxxxx"

# 1. Python Agent（先启动）
cd travel-agent-py
pip install -r requirements.txt
python server.py                    # :5000

# 2. Java 后端
cd travel-server-java
./mvnw spring-boot:run              # :8080

# 3. Vue 前端
cd travel-h5
npm install
npm run dev                         # :5174
```

浏览器打开 **http://localhost:5174**

### 测试账号

启动后自动创建：**`demo` / `demo123`**

---

## 📡 API

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | — | 注册 |
| POST | `/api/auth/login` | — | 登录，返回 JWT |
| POST | `/api/travel/recommend` | JWT | 旅游规划 |
| POST | `/api/travel/recommend/stream` | JWT | 流式规划（SSE 进度） |
| POST | `/api/travel/chat` | JWT | 流式对话（SSE） |
| GET | `/api/chat/sessions` | JWT | 历史会话列表 |
| GET | `/api/chat/sessions/{id}/messages` | JWT | 会话消息 |
| DELETE | `/api/chat/sessions/{id}` | JWT | 删除会话 |
| POST | `/api/favorites` | JWT | 添加收藏 |
| GET | `/api/favorites` | JWT | 收藏列表 |
| DELETE | `/api/favorites/{id}` | JWT | 删除收藏 |

---

## 📁 项目结构

```
├── travel-h5/                # Vue 3 前端
│   └── src/
│       ├── views/            # 7 页面（首页/详情/对话/我的/登录/注册/收藏）
│       ├── components/       # ChatBubble / SpotItem / BudgetTable
│       ├── stores/           # Pinia（auth / chat）
│       ├── router/           # Hash 路由 + beforeEach 守卫
│       └── utils/            # Axios（JWT 注入 + 401 处理）
├── travel-server-java/       # Spring Boot 网关
│   └── src/main/java/com/travel/server/
│       ├── controller/       # REST + SSE 端点（Travel / Auth / ChatHistory / Favorite）
│       ├── service/          # 业务逻辑 + Agent 响应解析
│       ├── gateway/          # OkHttp → Python Agent
│       ├── security/         # JWT 工具 + 过滤器 + SecurityConfig
│       ├── entity/           # JPA 实体（User / ChatMessage / Favorite）
│       ├── repository/       # Spring Data JPA
│       ├── config/           # CORS / 异常处理 / DataInitializer
│       └── task/             # 定时清理 >3 天消息
├── travel-agent-py/          # Python AI Agent
│   ├── agents/               # TravelAgent + ChatAgent
│   ├── tools/                # 5 工具 + 内置景点知识库
│   ├── memory/               # 多租户会话记忆
│   ├── rag/                  # ChromaDB 向量知识库
│   └── server.py             # FastAPI 入口
└── README.md
```

---

## 🧠 Agent 工作流

```
用户: "北京3天3000元"
  → RAG 检索城市知识
  → LLM 带工具调用
    → search_spot("故宫", "北京")  → 景点详情
    → check_ticket("故宫")         → 门票信息
    → calc_budget(3000, 3, "北京") → 预算分配
    → travel_plan_done             → 强制输出 JSON
  → 校验提取 JSON → 结构化行程
```

---

## 📝 待办

- [ ] Redis 缓存优化
- [ ] RAG 知识库扩展（美食/交通/贴士）
- [ ] Web 搜索接入真实 API

---

## 📄 License

MIT
