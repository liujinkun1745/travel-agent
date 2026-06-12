"""
对话 Agent — Memory上下文 + Tool Calling Loop + 流式输出
"""
from typing import Generator

from agents.base_agent import BaseAgent
from tools.travel_tools import (
    SEARCH_SPOT_TOOL, CHECK_TICKET_TOOL, SEARCH_WEB_TOOL
)
from rag.chroma_store import rag_store


CHAT_AGENT_PROMPT = """你是一个友好的旅游助手 Agent，名叫"小旅"。

你可以使用以下工具：
- search_spot：查询景点详情（门票、交通、介绍）
- check_ticket：确认门票预约信息
- search_web：查询最新攻略

回答原则（重要）：
- 简单问候、闲聊、通用常识问题 → **直接回答，不要调用工具**
- 询问具体景点信息 → 先调用工具查询，再回答
- 一次最多调用1个工具，拿到结果后立即给出回答
- 只调用有把握的工具，不重复调用相同工具
- 回答要具体实用，不要说你做不到的事情"""


class ChatAgent(BaseAgent):
    """旅游对话 Agent — 带记忆和工具调用"""

    def __init__(self):
        super().__init__(
            system_prompt=CHAT_AGENT_PROMPT,
            tools=[SEARCH_SPOT_TOOL, CHECK_TICKET_TOOL, SEARCH_WEB_TOOL],
            temperature=0.8,
            max_tool_rounds=5,  # 增加轮次，确保有机会输出最终答案
            rag_store=rag_store
        )

    def chat_stream(self, session_id: str, message: str) -> Generator[str, None, None]:
        """流式对话，RAG 增强"""
        rag_context = ""
        if rag_store:
            try:
                rag_results = rag_store.search(message, n_results=3)
                if rag_results:
                    rag_context = "\n".join([r['text'][:200] for r in rag_results])
            except Exception:
                pass

        if rag_context:
            message = f"{message}\n\n[参考]\n{rag_context}"

        yield from self.run_tool_loop_stream(session_id, message)


# 全局单例
chat_agent = ChatAgent()
