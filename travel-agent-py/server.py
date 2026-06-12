"""
旅游 Agent 服务 — FastAPI 入口
端口: 5000
"""
import json
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.travel_agent import travel_agent
from agents.chat_agent import chat_agent
from memory.session_memory import memory_manager
from rag.chroma_store import rag_store

# ==============================================
# FastAPI 应用
# ==============================================
app = FastAPI(
    title="旅游 Agent 服务",
    description="AI 旅游规划 Agent — Agent + Memory + RAG + Tool Calling",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================
# 请求模型
# ==============================================
class PlanRequest(BaseModel):
    city: str = Field(..., description="目的地城市", example="北京")
    budget: float = Field(..., ge=100, description="预算（元）", example=5000)
    days: int = Field(..., ge=1, le=30, description="旅行天数", example=3)
    session_id: Optional[str] = Field(None, description="会话ID")
    user_preferences: Optional[str] = Field(None, description="用户偏好")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息", example="北京有哪些必去的景点？")
    session_id: Optional[str] = Field(None, description="会话ID")


# ==============================================
# API 端点
# ==============================================
@app.get("/health")
def health():
    """健康检查"""
    rag_stats = {}
    try:
        rag_stats = rag_store.get_stats()
    except Exception:
        rag_stats = {"error": "RAG 未就绪"}

    return {
        "status": "ok",
        "service": "旅游 Agent 服务",
        "timestamp": time.time(),
        "rag": rag_stats,
        "active_sessions": len(memory_manager.sessions)
    }


@app.post("/agent/plan")
def agent_plan(request: PlanRequest):
    """
    旅游规划 Agent
    Flow: RAG → Plan → LLM ⇄ Tool → Validate → JSON
    """
    session_id = request.session_id or f"plan_{request.city}_{int(time.time())}"

    try:
        result = travel_agent.plan(
            session_id=session_id,
            city=request.city,
            budget=request.budget,
            days=request.days
        )
        result["session_id"] = session_id  # 返回 session_id 供后续复用
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 规划失败: {str(e)}")


@app.post("/agent/plan/stream")
def agent_plan_stream(request: PlanRequest):
    """
    流式旅游规划 Agent
    返回 SSE 事件流：progress → progress → ... → result/error
    """
    session_id = request.session_id or f"plan_{request.city}_{int(time.time())}"

    def generate():
        try:
            for event in travel_agent.plan_stream(
                session_id=session_id,
                city=request.city,
                budget=request.budget,
                days=request.days
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/agent/chat")
def agent_chat(request: ChatRequest):
    """
    对话 Agent（SSE 流式）
    含 Memory 上下文 + Tool Calling
    """
    session_id = request.session_id or f"chat_{int(time.time())}"

    def generate():
        try:
            for chunk in chat_agent.chat_stream(session_id, request.message):
                event = {"type": "chunk", "content": chunk}
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            # 发送完成信号
            done = {"type": "done"}
            yield f"data: {json.dumps(done)}\n\n"

        except Exception as e:
            error = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/agent/history/{session_id}")
def get_history(session_id: str):
    """获取会话历史"""
    session = memory_manager.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return {
        "session_id": session_id,
        "context": session.context,
        "messages": [
            {"role": m.role, "content": m.content[:500], "timestamp": m.timestamp}
            for m in session.messages[-20:]
        ]
    }


@app.get("/agent/stats")
def get_stats():
    """Agent 统计信息"""
    return {
        "rag_stats": rag_store.get_stats(),
        "active_sessions": len(memory_manager.sessions),
        "total_messages": sum(len(s.messages) for s in memory_manager.sessions.values()),
    }


# ==============================================
# 启动
# ==============================================
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  旅游 Agent 服务启动中...")
    print("  Agent + Memory + RAG + Tool Calling")
    print("  端口: 5000")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=5000)
