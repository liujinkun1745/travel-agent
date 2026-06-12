"""
Agent 基类 — 实现 LLM ⇄ Tool 回路
"""
import json
import os
from abc import ABC
from typing import List, Dict, Optional, Generator

from openai import OpenAI

from memory.session_memory import MemoryManager, memory_manager
from tools.travel_tools import ALL_TOOLS, TOOL_EXECUTORS


# 工具名称 → 中文显示名映射（用于进度通知）
_TOOL_DISPLAY_NAMES = {
    "search_spot": "景点信息",
    "check_ticket": "门票价格",
    "calc_budget": "预算方案",
    "search_web": "攻略信息",
    "travel_plan_done": "行程方案",
}


class BaseAgent(ABC):
    """LLM Agent 基类，提供 Tool Calling Loop"""

    def __init__(
        self,
        system_prompt: str,
        tools: List[Dict] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tool_rounds: int = 5,
        mem: MemoryManager = None,
        rag_store=None,
        done_tool_names: set = None
    ):
        self.system_prompt = system_prompt
        self.tools = tools or ALL_TOOLS
        self.model = model
        self.temperature = temperature
        self.max_tool_rounds = max_tool_rounds
        self.memory = mem or memory_manager
        self.rag_store = rag_store
        self.done_tool_names = done_tool_names or set()

        # 优先使用 DEEPSEEK_API_KEY，否则使用 SILICONFLOW_API_KEY
        deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
        siliconflow_key = os.environ.get("SILICONFLOW_API_KEY")

        if deepseek_key:
            api_key = deepseek_key
            base_url = "https://api.deepseek.com/v1"
        elif siliconflow_key:
            api_key = siliconflow_key
            base_url = "https://api.siliconflow.cn/v1"
        else:
            raise ValueError(
                "未设置 DEEPSEEK_API_KEY 或 SILICONFLOW_API_KEY 环境变量，"
                "请至少配置一个后再启动 Agent 服务"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=180.0
        )

    def _call_llm(self, messages: List[Dict], stream: bool = False, tools: List[Dict] = None):
        """调用 LLM，支持 tool calling"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 4096,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if stream:
            kwargs["stream"] = True

        try:
            return self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"LLM API 调用失败: {str(e)}") from e

    def _execute_tool(self, tool_call) -> str:
        """执行单个 tool call"""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        # 仅给接受 rag_store 参数的工具注入（目前只有 search_spot）
        if self.rag_store is not None and name in ("search_spot",):
            args["rag_store"] = self.rag_store

        executor = TOOL_EXECUTORS.get(name)
        if executor:
            try:
                return executor(**args)
            except Exception as e:
                return json.dumps({"error": f"工具执行失败: {str(e)}"})
        return json.dumps({"error": f"未知工具: {name}"})

    def run_tool_loop(self, session_id: str, user_message: str, on_progress=None) -> str:
        """
        执行 Agent Tool Calling Loop:
        1. 发送消息 + tools → LLM
        2. 如果 LLM 返回 tool_call → 执行工具 → 结果追加到消息 → 回到步骤 1
        3. 如果 LLM 返回文本 → 完成，返回结果

        on_progress: 可选回调 (step, message)，用于流式进度通知
        """
        session = self.memory.get_or_create_session(session_id)

        # 进度通知：开始规划
        if on_progress:
            on_progress("planning", "正在分析需求，制定规划方案...")

        # 构建初始消息
        messages = [{"role": "system", "content": self.system_prompt}]

        # 添加旅行上下文
        ctx = session.get_context_str()
        if ctx:
            messages.append({"role": "system", "content": f"当前旅行信息: {ctx}"})

        # 添加历史消息
        messages.extend(session.get_messages_for_llm(max_turns=10))

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        session.add_message("user", user_message)

        # Tool Calling Loop
        for round_num in range(self.max_tool_rounds):
            response = self._call_llm(messages, tools=self.tools)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                # LLM 要求调用工具
                tool_calls = choice.message.tool_calls

                # 进度通知：工具调用
                if on_progress:
                    tool_names = [tc.function.name for tc in tool_calls]
                    for name in tool_names:
                        display = _TOOL_DISPLAY_NAMES.get(name, name)
                        on_progress("tool", f"正在查询{display}...")

                # 记录 assistant 的 tool_calls 请求
                session.add_message(
                    "assistant", "",
                    tool_calls=[{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in tool_calls]
                )

                # 添加 assistant 消息到 LLM 上下文
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in tool_calls]
                })

                # 执行每个工具调用
                for tc in tool_calls:
                    tool_result = self._execute_tool(tc)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result
                    })
                    # 也记录到会话记忆
                    session.add_message("tool", tool_result, tool_call_id=tc.id)

                # 如果调用了"完成"类工具，强制 LLM 输出最终文本（不带 tools）
                if any(tc.function.name in self.done_tool_names for tc in tool_calls):
                    # 进度通知：生成最终结果
                    if on_progress:
                        on_progress("generate", "正在生成最终行程方案...")
                    messages.append({
                        "role": "user",
                        "content": "请直接输出最终结果，不要调用任何工具。"
                    })
                    final_response = self._call_llm(messages, stream=False, tools=None)
                    content = final_response.choices[0].message.content or ""
                    session.add_message("assistant", content)
                    return content

                # 继续循环，让 LLM 处理工具结果
                continue

            # LLM 返回了最终文本响应
            content = choice.message.content or ""
            session.add_message("assistant", content)
            return content

        # 达到最大轮次仍无结果 → 最后一次尝试：强制输出文本（不带 tools）
        messages.append({
            "role": "user",
            "content": "请基于以上所有查询结果，直接给出完整回答，不要调用任何工具。"
        })
        final_response = self._call_llm(messages, stream=False, tools=None)
        content = final_response.choices[0].message.content or ""
        session.add_message("assistant", content)
        return content

    def run_tool_loop_stream(self, session_id: str, user_message: str) -> Generator[str, None, None]:
        """流式版本的 Tool Calling Loop"""
        session = self.memory.get_or_create_session(session_id)

        messages = [{"role": "system", "content": self.system_prompt}]
        ctx = session.get_context_str()
        if ctx:
            messages.append({"role": "system", "content": f"当前旅行信息: {ctx}"})
        messages.extend(session.get_messages_for_llm(max_turns=10))
        messages.append({"role": "user", "content": user_message})
        session.add_message("user", user_message)

        # Tool Calling Loop（非流式处理工具调用）
        full_response = ""
        round_num = 0
        while round_num < self.max_tool_rounds:
            response = self._call_llm(messages, tools=self.tools)
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                # 最后一轮：强制 LLM 基于已有信息直接回答（不带 tools）
                if round_num >= self.max_tool_rounds - 1:
                    # 记录最后的 tool_calls 到会话记忆和消息历史
                    tool_calls = choice.message.tool_calls
                    session.add_message(
                        "assistant", "",
                        tool_calls=[{
                            "id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                        } for tc in tool_calls]
                    )
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tc.id, "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                        } for tc in tool_calls]
                    })
                    # 执行工具获取结果
                    for tc in tool_calls:
                        tool_result = self._execute_tool(tc)
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_result})
                        session.add_message("tool", tool_result, tool_call_id=tc.id)
                    # 追加强制回答提示，然后不带 tools 再调一次 LLM
                    messages.append({
                        "role": "user",
                        "content": "请基于以上查询结果，直接给出完整回答，不要调用任何工具。"
                    })
                    final_response = self._call_llm(messages, stream=False, tools=None)
                    content = final_response.choices[0].message.content or ""
                    full_response = content
                    break

                tool_calls = choice.message.tool_calls
                # 记录 assistant 的 tool_calls 到会话记忆
                session.add_message(
                    "assistant", "",
                    tool_calls=[{
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in tool_calls]
                )
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in tool_calls]
                })
                for tc in tool_calls:
                    tool_result = self._execute_tool(tc)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_result})
                    # 记录 tool 结果到会话记忆
                    session.add_message("tool", tool_result, tool_call_id=tc.id)
                round_num += 1
                continue

            content = choice.message.content or ""
            full_response = content
            break

        if not full_response:
            full_response = "抱歉，规划过程超时，请简化需求后重试。"

        session.add_message("assistant", full_response)

        # 流式输出最终结果（模拟打字机效果）
        chunk_size = 3
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i:i + chunk_size]
