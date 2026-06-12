"""
旅游 Agent 工具集
每个工具包含: name, description, parameters_schema, execute 函数
"""
import json
from typing import Any, Dict

# ==============================================
# 景点知识库（RAG 提供，这里做 fallback）
# ==============================================
_SPOT_KNOWLEDGE = {
    "故宫": {
        "name": "故宫博物院",
        "city": "北京",
        "ticket": "旺季60元，淡季40元",
        "duration": "3-4小时",
        "transportation": "地铁1号线天安门东站",
        "description": "明清皇家宫殿，世界文化遗产，9000余间房屋",
        "tips": "必须提前在公众号预约，无现场售票",
        "rating": 4.9
    },
    "天安门": {
        "name": "天安门广场",
        "city": "北京",
        "ticket": "免费（需预约）",
        "duration": "1-2小时",
        "transportation": "地铁1号线天安门东站/天安门西站",
        "description": "世界最大城市广场，可参观人民英雄纪念碑、毛主席纪念堂",
        "tips": "安检严格，携带身份证",
        "rating": 4.8
    },
    "颐和园": {
        "name": "颐和园",
        "city": "北京",
        "ticket": "旺季30元，淡季20元",
        "duration": "2-3小时",
        "transportation": "地铁4号线北宫门站",
        "description": "中国古典园林典范，以昆明湖和万寿山为核心",
        "tips": "面积较大，建议穿运动鞋",
        "rating": 4.7
    },
    "西湖": {
        "name": "西湖",
        "city": "杭州",
        "ticket": "免费（部分景点收费）",
        "duration": "半天",
        "transportation": "地铁1号线龙翔桥站",
        "description": "中国最著名的湖泊景观，十景闻名天下",
        "tips": "建议骑行或步行游览，避开节假日高峰",
        "rating": 4.9
    },
    "兵马俑": {
        "name": "秦始皇兵马俑博物馆",
        "city": "西安",
        "ticket": "120元",
        "duration": "2-3小时",
        "transportation": "公交游5路/306路",
        "description": "世界第八大奇迹，秦始皇陵陪葬坑",
        "tips": "距市区40公里，建议预留半天时间",
        "rating": 4.9
    },
    "外滩": {
        "name": "外滩",
        "city": "上海",
        "ticket": "免费",
        "duration": "1-2小时",
        "transportation": "地铁2号线/10号线南京东路站",
        "description": "黄浦江畔，万国建筑博览群，陆家嘴天际线",
        "tips": "白天和夜景各有特色，推荐黄昏时分前往",
        "rating": 4.7
    },
    "大熊猫繁育基地": {
        "name": "大熊猫繁育研究基地",
        "city": "成都",
        "ticket": "55元",
        "duration": "2-3小时",
        "transportation": "地铁3号线熊猫大道站转景区直通车",
        "description": "近距离观赏国宝大熊猫，包括幼崽",
        "tips": "上午9-10点是大熊猫最活跃的时间",
        "rating": 4.8
    },
}

# ==============================================
# Tool: search_spot
# ==============================================
SEARCH_SPOT_TOOL = {
    "type": "function",
    "function": {
        "name": "search_spot",
        "description": "搜索景点详细信息：门票价格、开放时间、交通方式、游览建议等",
        "parameters": {
            "type": "object",
            "properties": {
                "spot_name": {
                    "type": "string",
                    "description": "景点名称，如：故宫、西湖"
                },
                "city": {
                    "type": "string",
                    "description": "所在城市，如：北京"
                }
            },
            "required": ["spot_name", "city"]
        }
    }
}

def execute_search_spot(spot_name: str, city: str = "", rag_store=None) -> str:
    """搜索景点信息，优先从 RAG 检索，fallback 到内置知识库"""
    # 优先 RAG
    if rag_store:
        rag_result = rag_store.search(f"{spot_name} {city}")
        if rag_result:
            return json.dumps(rag_result, ensure_ascii=False)

    # Fallback 到内置知识库
    for key, info in _SPOT_KNOWLEDGE.items():
        if key in spot_name or spot_name in key:
            if not city or city in info.get("city", ""):
                return json.dumps(info, ensure_ascii=False, indent=2)

    # 未找到时返回通用模板
    return json.dumps({
        "name": spot_name,
        "city": city or "未知",
        "ticket": "请查看官方渠道",
        "duration": "1-3小时",
        "transportation": f"建议查询{spot_name}的具体交通方式",
        "description": f"{spot_name}是{city}的热门景点",
        "tips": "建议提前预约门票，避开节假日高峰"
    }, ensure_ascii=False, indent=2)


# ==============================================
# Tool: check_ticket
# ==============================================
CHECK_TICKET_TOOL = {
    "type": "function",
    "function": {
        "name": "check_ticket",
        "description": "查询景点最新门票价格、是否需要预约、购买方式",
        "parameters": {
            "type": "object",
            "properties": {
                "spot_name": {
                    "type": "string",
                    "description": "景点名称"
                }
            },
            "required": ["spot_name"]
        }
    }
}

def execute_check_ticket(spot_name: str) -> str:
    """查询门票信息"""
    for key, info in _SPOT_KNOWLEDGE.items():
        if key in spot_name or spot_name in key:
            return json.dumps({
                "spot": info["name"],
                "ticket": info["ticket"],
                "booking": info["tips"],
                "status": "需要预约" if "预约" in info["tips"] else "可现场购票"
            }, ensure_ascii=False, indent=2)

    return json.dumps({
        "spot": spot_name,
        "ticket": "建议查询官方渠道获取最新价格",
        "booking": "建议提前确认是否需要预约",
        "status": "未知"
    }, ensure_ascii=False, indent=2)


# ==============================================
# Tool: calc_budget
# ==============================================
CALC_BUDGET_TOOL = {
    "type": "function",
    "function": {
        "name": "calc_budget",
        "description": "根据天数和预算，核算住宿、餐饮、交通、门票的合理分配比例",
        "parameters": {
            "type": "object",
            "properties": {
                "total_budget": {
                    "type": "number",
                    "description": "总预算（元）"
                },
                "days": {
                    "type": "integer",
                    "description": "旅行天数"
                },
                "city": {
                    "type": "string",
                    "description": "城市"
                }
            },
            "required": ["total_budget", "days", "city"]
        }
    }
}

def execute_calc_budget(total_budget: float, days: int, city: str = "") -> str:
    """预算核算"""
    # 一线城市住宿费用偏高
    tier1_cities = ["北京", "上海", "广州", "深圳", "杭州"]
    hotel_per_night = 300 if city in tier1_cities else 200

    accommodation = hotel_per_night * days
    remaining = total_budget - accommodation

    food = int(remaining * 0.35)
    transport = int(remaining * 0.20)
    tickets = int(remaining * 0.25)
    other = int(remaining * 0.20)

    # 调整使总和匹配
    total_computed = accommodation + food + transport + tickets + other
    diff = int(total_budget) - total_computed
    other += diff

    return json.dumps({
        "city": city,
        "days": days,
        "total_budget": int(total_budget),
        "breakdown": {
            "accommodation": accommodation,
            "food": food,
            "transportation": transport,
            "tickets": tickets,
            "other": other
        },
        "per_night_hotel": hotel_per_night,
        "note": "一线城市住宿费已按较高标准核算" if city in tier1_cities else "住宿按经济型酒店标准"
    }, ensure_ascii=False, indent=2)


# ==============================================
# Tool: search_web
# ==============================================
SEARCH_WEB_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "搜索最新旅游攻略、实时信息（天气、活动、交通状况等）",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    }
}

def execute_search_web(query: str) -> str:
    """Web 搜索 — 当前用内置数据模拟，可接入真实搜索 API"""
    # 简化的模拟搜索结果
    tips_db = {
        "北京美食": "推荐：北京烤鸭（全聚德/便宜坊）、炸酱面、豆汁焦圈、卤煮火烧、涮羊肉（东来顺）",
        "上海美食": "推荐：小笼包（南翔馒头店）、生煎包、本帮红烧肉、葱油拌面、蟹壳黄",
        "成都美食": "推荐：火锅、串串香、担担面、龙抄手、麻婆豆腐、夫妻肺片",
        "杭州美食": "推荐：西湖醋鱼、龙井虾仁、东坡肉、叫花鸡、片儿川",
        "西安美食": "推荐：肉夹馍、羊肉泡馍、凉皮、Biangbiang面、葫芦头",
        "天气": "建议出发前3天查看天气预报，中国天气网: weather.com.cn",
        "交通": "主要城市地铁覆盖完善，推荐使用高德地图/百度地图导航",
        "住宿": "推荐提前在携程/去哪儿预订，旺季价格会上涨30-50%",
        "签证": "中国大陆居民持身份证即可出行，无需签证",
        "保险": "推荐购买旅游意外险，支付宝/微信可在线购买，约10-50元/天",
    }

    for key, value in tips_db.items():
        # 双向匹配：关键词包含在 query 中，或 query 包含在关键词中
        if key in query or query in key:
            return json.dumps({"query": query, "result": value}, ensure_ascii=False)

    return json.dumps({
        "query": query,
        "result": f"关于「{query}」的建议：建议出行前通过携程/马蜂窝/小红书等平台获取最新攻略信息。"
    }, ensure_ascii=False, indent=2)


# ==============================================
# Tool: travel_plan_done (Goal completion marker)
# ==============================================
PLAN_DONE_TOOL = {
    "type": "function",
    "function": {
        "name": "travel_plan_done",
        "description": "当旅游规划完成并准备好 JSON 输出时调用此工具，标记任务完成",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "简要总结已完成的规划内容"
                }
            },
            "required": ["summary"]
        }
    }
}

def execute_travel_plan_done(summary: str) -> str:
    return json.dumps({"status": "done", "summary": summary}, ensure_ascii=False)


# ==============================================
# 工具注册表
# ==============================================
ALL_TOOLS = [
    SEARCH_SPOT_TOOL,
    CHECK_TICKET_TOOL,
    CALC_BUDGET_TOOL,
    SEARCH_WEB_TOOL,
    PLAN_DONE_TOOL,
]

TOOL_EXECUTORS = {
    "search_spot": execute_search_spot,
    "check_ticket": execute_check_ticket,
    "calc_budget": execute_calc_budget,
    "search_web": execute_search_web,
    "travel_plan_done": execute_travel_plan_done,
}
