"""
旅游规划 Agent — RAG检索 → 提示词组装 → LLM⇄Tool回路 → JSON校验

Flow: RAGRetrieve → PlanBuild → LLM⇄ToolNode → ValidateNode
"""
import json
import re
from typing import Dict, Optional, Generator
from queue import Queue
from threading import Thread

from agents.base_agent import BaseAgent
from tools.travel_tools import (
    SEARCH_SPOT_TOOL, CHECK_TICKET_TOOL, CALC_BUDGET_TOOL, PLAN_DONE_TOOL
)
from rag.chroma_store import rag_store


TRAVEL_PLANNER_PROMPT = """你是一个旅游规划 API。你接收用户请求，调用工具获取数据，然后输出 JSON。

步骤：
1. 用 search_spot 查询所有景点信息
2. 用 check_ticket 确认门票
3. 用 calc_budget 核算预算
4. 最终输出 **一行纯 JSON**，不含任何其他文字

**输出格式（严格遵守，不要 markdown，不要解释）：**
{"success":true,"city":"城市","days":N,"totalBudget":N,"dailyItinerary":[{"day":1,"date":"第1天","morning":{"spot":"景点","duration":"时长","ticket":"价格","transportation":"交通","description":"介绍"},"afternoon":{...},"evening":{...}}],"budgetBreakdown":{"accommodation":N,"food":N,"transportation":N,"tickets":N,"other":N},"tips":["..."],"warnings":["..."]}

**规则（违反将导致解析失败）：**
- 最终输出必须是纯 JSON，不能包含 markdown、表格、``` 标记或任何说明文字
- 每个景点的 spot/duration/ticket/transportation/description 必须来自工具查询
- 交通必须具体到"地铁X号线XX站"
- 预算各项之和必须等于 totalBudget"""


class TravelAgent(BaseAgent):
    """旅游规划 Agent"""

    def __init__(self):
        super().__init__(
            system_prompt=TRAVEL_PLANNER_PROMPT,
            tools=[SEARCH_SPOT_TOOL, CHECK_TICKET_TOOL, CALC_BUDGET_TOOL, PLAN_DONE_TOOL],
            temperature=0.7,
            max_tool_rounds=10,  # 规划需要多轮工具调用
            rag_store=rag_store,
            done_tool_names={"travel_plan_done"}
        )

    def plan(self, session_id: str, city: str, budget: float, days: int) -> Dict:
        """生成旅游规划，返回结构化数据"""
        # 设置旅行上下文
        self.memory.set_travel_context(session_id, city, budget, days)

        # Step 1: RAG 检索 — 获取城市背景知识
        rag_context = ""
        if rag_store:
            rag_results = rag_store.search(f"{city} 旅游 景点 攻略", n_results=5)
            if rag_results:
                rag_context = "\n".join([f"- {r['text'][:300]}" for r in rag_results])

        # Step 2: 构建增强提示词
        rag_section = ""
        if rag_context:
            rag_section = "参考信息（来自知识库）：\n" + rag_context

        user_message = f"""请为我规划一次旅行：
- 目的地：{city}
- 预算：{budget}元
- 天数：{days}天

{rag_section}

请严格按照流程：先用工具查询景点信息，再输出完整 JSON 行程。"""

        # Step 3: Agent Tool Calling Loop
        response_text = self.run_tool_loop(session_id, user_message)

        # Step 4: JSON 提取和校验
        return self._parse_and_validate(response_text, city, budget, days)

    def plan_stream(self, session_id: str, city: str, budget: float, days: int) -> Generator:
        """流式版本的旅游规划 — 通过 SSE 推送进度事件"""
        q = Queue()

        def progress_callback(step, message):
            q.put({"type": "progress", "step": step, "message": message})

        def run():
            try:
                self.memory.set_travel_context(session_id, city, budget, days)

                # RAG 检索
                q.put({"type": "progress", "step": "rag",
                        "message": f"正在检索{city}的旅游信息..."})
                rag_context = ""
                if rag_store:
                    rag_results = rag_store.search(f"{city} 旅游 景点 攻略", n_results=5)
                    if rag_results:
                        rag_context = "\n".join([f"- {r['text'][:300]}" for r in rag_results])

                rag_section = ""
                if rag_context:
                    rag_section = "参考信息（来自知识库）：\n" + rag_context

                user_message = f"""请为我规划一次旅行：
- 目的地：{city}
- 预算：{budget}元
- 天数：{days}天

{rag_section}

请严格按照流程：先用工具查询景点信息，再输出完整 JSON 行程。"""

                response_text = self.run_tool_loop(session_id, user_message,
                                                    on_progress=progress_callback)
                result = self._parse_and_validate(response_text, city, budget, days)
                result["session_id"] = session_id
                q.put({"type": "result", "data": result})
            except Exception as e:
                q.put({"type": "error", "message": str(e)})

        # 后台线程执行规划
        t = Thread(target=run, daemon=True)
        t.start()

        # 主线程 yield SSE 事件
        while True:
            item = q.get()
            yield item
            if item["type"] in ("result", "error"):
                break

    def _parse_and_validate(self, response: str, city: str, budget: float, days: int) -> Dict:
        """从 Agent 响应中提取 JSON 并校验"""
        result = {
            "success": False,
            "city": city,
            "days": days,
            "totalBudget": int(budget),
            "error": None,
            "rawResponse": response
        }

        try:
            # JSON 提取降级链（兼容更多 LLM 输出格式）
            json_str = None
            patterns = [
                r'```json\s*([\s\S]*?)```',   # ```json ... ``` (灵活空白)
                r'```\s*([\s\S]*?)```',       # ``` ... ``` (灵活空白)
            ]
            for p in patterns:
                m = re.search(p, response)
                if m:
                    json_str = m.group(1).strip()
                    break

            if not json_str:
                # 尝试找到最外层的 { ... } 配对
                start = response.find('{')
                end = response.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_str = response[start:end + 1]

            if json_str:
                data = json.loads(json_str)

                # 校验必要字段
                if "dailyItinerary" in data and len(data["dailyItinerary"]) > 0:
                    result["success"] = True
                    result["city"] = data.get("city", city)
                    result["days"] = data.get("days", days)
                    result["totalBudget"] = data.get("totalBudget", int(budget))
                    result["dailyItinerary"] = data.get("dailyItinerary", [])
                    result["budgetBreakdown"] = data.get("budgetBreakdown", {})
                    result["tips"] = data.get("tips", [])
                    result["warnings"] = data.get("warnings", [])
                    result["error"] = None
                else:
                    result["error"] = "AI 未返回有效行程数据"
            else:
                result["error"] = "未能从 Agent 响应中提取 JSON"

        except json.JSONDecodeError as e:
            result["error"] = f"JSON 解析失败: {str(e)}"
        except Exception as e:
            result["error"] = f"规划校验失败: {str(e)}"

        return result


# 全局单例
travel_agent = TravelAgent()
