package com.travel.server.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.travel.server.gateway.AgentGateway;
import com.travel.server.vo.TravelRecommendVO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * 旅游推荐服务
 * 对接 Python Agent 服务（Agent + Memory + RAG + Tool Calling）
 */
@Service
public class TravelService {

    private static final Logger log = LoggerFactory.getLogger(TravelService.class);

    private final AgentGateway agentGateway;

    public TravelService(AgentGateway agentGateway) {
        this.agentGateway = agentGateway;
    }

    /**
     * 生成旅游规划 — 通过 Python Agent
     */
    public TravelRecommendVO recommend(String city, Double budget, Integer days) {
        try {
            JsonNode response = agentGateway.plan(city, budget, days, null);
            return parseAgentResponse(response);
        } catch (IOException e) {
            log.error("Agent 规划失败", e);
            TravelRecommendVO errorResult = new TravelRecommendVO();
            errorResult.setSuccess(false);
            errorResult.setError("Agent 服务暂时不可用: " + e.getMessage());
            return errorResult;
        }
    }

    /**
     * 流式 AI 对话 — 通过 Python Agent
     */
    public void chat(String message, String sessionId, Consumer<String> chunkConsumer) throws IOException {
        agentGateway.chat(message, sessionId, chunkConsumer);
    }

    /**
     * 流式旅游规划 — 通过 Python Agent SSE
     */
    public void recommendStream(String city, Double budget, Integer days,
                                 Consumer<String> progressConsumer,
                                 Consumer<TravelRecommendVO> resultConsumer) throws IOException {
        agentGateway.planStream(city, budget, days, null,
                progressConsumer,
                resultData -> {
                    TravelRecommendVO vo = parseAgentResponse(resultData);
                    resultConsumer.accept(vo);
                }
        );
    }

    /**
     * 解析 Agent 返回的 JSON → TravelRecommendVO
     */
    private TravelRecommendVO parseAgentResponse(JsonNode node) {
        TravelRecommendVO result = new TravelRecommendVO();

        try {
            boolean success = node.path("success").asBoolean(false);

            if (success) {
                result.setSuccess(true);
                result.setCity(node.path("city").asText());
                // 保存 sessionId 供后续对话复用
                if (node.has("session_id") && !node.path("session_id").isNull()) {
                    result.setSessionId(node.path("session_id").asText());
                }
                // 使用 has() + asInt() 区分"字段缺失"和"值为 0"
                if (node.has("days") && !node.path("days").isNull()) {
                    result.setDays(node.path("days").asInt());
                }
                if (node.has("totalBudget") && !node.path("totalBudget").isNull()) {
                    result.setTotalBudget(node.path("totalBudget").asInt());
                }

                // 解析每日行程
                JsonNode itinerary = node.path("dailyItinerary");
                if (itinerary.isArray()) {
                    List<TravelRecommendVO.DailyItinerary> days = new ArrayList<>();
                    for (JsonNode dayNode : itinerary) {
                        TravelRecommendVO.DailyItinerary day = new TravelRecommendVO.DailyItinerary();
                        day.setDay(dayNode.path("day").asInt());
                        day.setDate(dayNode.path("date").asText());
                        day.setMorning(parseTimeSlot(dayNode.path("morning")));
                        day.setAfternoon(parseTimeSlot(dayNode.path("afternoon")));
                        day.setEvening(parseTimeSlot(dayNode.path("evening")));
                        days.add(day);
                    }
                    result.setDailyItinerary(days);
                }

                // 解析预算明细
                JsonNode budget = node.path("budgetBreakdown");
                TravelRecommendVO.BudgetBreakdown breakdown = new TravelRecommendVO.BudgetBreakdown();
                breakdown.setAccommodation(budget.path("accommodation").asInt());
                breakdown.setFood(budget.path("food").asInt());
                breakdown.setTransportation(budget.path("transportation").asInt());
                breakdown.setTickets(budget.path("tickets").asInt());
                breakdown.setOther(budget.path("other").asInt());
                result.setBudgetBreakdown(breakdown);

                // 解析 tips / warnings
                result.setTips(jsonArrayToList(node.path("tips")));
                result.setWarnings(jsonArrayToList(node.path("warnings")));

            } else {
                result.setSuccess(false);
                result.setError(node.path("error").asText("未知错误"));
                String raw = node.path("rawResponse").asText(null);
                if (raw != null) {
                    result.setRawResponse(raw);
                }
            }
        } catch (Exception e) {
            log.error("解析 Agent 响应失败", e);
            result.setSuccess(false);
            result.setError("Agent 响应解析失败: " + e.getMessage());
        }

        return result;
    }

    private TravelRecommendVO.TimeSlot parseTimeSlot(JsonNode node) {
        if (node == null || node.isNull() || node.isMissingNode()) return null;
        TravelRecommendVO.TimeSlot slot = new TravelRecommendVO.TimeSlot();
        slot.setSpot(node.path("spot").asText());
        slot.setDuration(node.path("duration").asText());
        slot.setTicket(node.path("ticket").asText());
        slot.setTransportation(node.path("transportation").asText());
        slot.setDescription(node.path("description").asText());
        return slot;
    }

    private List<String> jsonArrayToList(JsonNode node) {
        List<String> list = new ArrayList<>();
        if (node != null && node.isArray()) {
            for (JsonNode item : node) {
                list.add(item.asText());
            }
        }
        return list;
    }
}
