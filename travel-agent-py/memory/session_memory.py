"""
会话记忆管理 — 支持多租户、多轮对话
"""
import time
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str           # system / user / assistant / tool
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class Session:
    session_id: str
    user_id: str = "default"
    messages: List[Message] = field(default_factory=list)
    context: dict = field(default_factory=dict)  # 旅行上下文 {city, budget, days}
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str, **kwargs):
        self.messages.append(Message(role=role, content=content, **kwargs))
        self.last_active = time.time()

    def get_messages_for_llm(self, max_turns: int = 20, include_tools: bool = False) -> List[dict]:
        """将消息转为 OpenAI 兼容格式，保留最近 N 轮

        Args:
            max_turns: 最大对话轮数
            include_tools: 是否包含 tool 消息（当前 tool loop 中为 True，加载历史时为 False）
        """
        recent = self.messages[-max_turns * 2:]
        result = []
        for msg in recent:
            # 加载历史时跳过 tool 消息（避免多轮对话中 tool 配对校验失败）
            # 同时跳过仅有 tool_calls 无内容的 assistant 消息（没 tool 结果配对无意义）
            if not include_tools:
                if msg.role == "tool":
                    continue
                if msg.role == "assistant" and not msg.content and msg.tool_calls:
                    continue
            item = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                item["tool_calls"] = msg.tool_calls
            result.append(item)
        return result

    def get_context_str(self) -> str:
        """获取当前旅行上下文的文本表示"""
        if not self.context:
            return ""
        parts = [f"{k}: {v}" for k, v in self.context.items() if v]
        return " | ".join(parts) if parts else ""

    def clear_old_sessions(self, max_age_seconds: int = 3600):
        """清理当前会话中的过期消息（注意：方法名有歧义，实际仅清理当前 Session 的消息，而非清理多个 Session）"""
        now = time.time()
        self.messages = [m for m in self.messages if now - m.timestamp < max_age_seconds]


class MemoryManager:
    """多租户记忆管理器"""

    def __init__(self, max_sessions: int = 1000):
        self.sessions: Dict[str, Session] = {}
        self.max_sessions = max_sessions

    def get_or_create_session(self, session_id: str = None, user_id: str = "default") -> Session:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        sid = session_id or self._generate_id(user_id)
        session = Session(session_id=sid, user_id=user_id)
        self.sessions[sid] = session

        # 超过上限时清理最旧的会话
        if len(self.sessions) > self.max_sessions:
            oldest = min(self.sessions.values(), key=lambda s: s.last_active)
            del self.sessions[oldest.session_id]

        return session

    def set_travel_context(self, session_id: str, city: str, budget: float, days: int):
        session = self.get_or_create_session(session_id)
        session.context = {"city": city, "budget": budget, "days": days}

    def _generate_id(self, user_id: str) -> str:
        raw = f"{user_id}_{time.time()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


# 全局单例
memory_manager = MemoryManager()
