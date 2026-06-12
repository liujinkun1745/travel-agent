package com.travel.server.gateway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

/**
 * Agent 网关 — 调用 Python Agent 服务 (localhost:5000)
 * 替代直接调大模型 API，由 Agent 层负责 Tool Calling + RAG + Memory
 */
@Component
public class AgentGateway {

    private static final Logger log = LoggerFactory.getLogger(AgentGateway.class);

    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final String agentBaseUrl;

    public AgentGateway(
            ObjectMapper objectMapper,
            @Value("${agent.base-url:http://localhost:5000}") String agentBaseUrl,
            @Value("${agent.connect-timeout:30}") int connectTimeout,
            @Value("${agent.read-timeout:180}") int readTimeout) {

        this.objectMapper = objectMapper;
        // 移除尾部斜杠，避免 URL 拼接时出现 "//"
        this.agentBaseUrl = agentBaseUrl.endsWith("/")
                ? agentBaseUrl.substring(0, agentBaseUrl.length() - 1)
                : agentBaseUrl;

        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(connectTimeout, TimeUnit.SECONDS)
                .readTimeout(readTimeout, TimeUnit.SECONDS)
                .build();
    }

    /**
     * 调用 Agent 旅游规划
     * POST /agent/plan
     */
    public JsonNode plan(String city, Double budget, Integer days, String sessionId) throws IOException {
        Map<String, Object> body = new HashMap<>();
        body.put("city", city);
        body.put("budget", budget);
        body.put("days", days);
        if (sessionId != null) {
            body.put("session_id", sessionId);
        }

        String json = objectMapper.writeValueAsString(body);
        Request request = new Request.Builder()
                .url(agentBaseUrl + "/agent/plan")
                .post(RequestBody.create(json, MediaType.parse("application/json")))
                .build();

        log.debug("Agent 规划请求: {}", json);

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "{}";
            if (!response.isSuccessful()) {
                log.error("Agent 规划失败: HTTP {} - {}", response.code(), responseBody);
                throw new IOException("Agent 规划失败: " + responseBody);
            }
            return objectMapper.readTree(responseBody);
        }
    }

    /**
     * 调用 Agent 对话（流式 SSE）
     * POST /agent/chat
     */
    public void chat(String message, String sessionId, Consumer<String> chunkConsumer) throws IOException {
        Map<String, Object> body = new HashMap<>();
        body.put("message", message);
        if (sessionId != null) {
            body.put("session_id", sessionId);
        }

        String json = objectMapper.writeValueAsString(body);
        Request request = new Request.Builder()
                .url(agentBaseUrl + "/agent/chat")
                .post(RequestBody.create(json, MediaType.parse("application/json")))
                .header("Accept", "text/event-stream")
                .build();

        log.debug("Agent 对话请求: {}", json);

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String errorBody = response.body() != null ? response.body().string() : "";
                throw new IOException("Agent 对话失败: HTTP " + response.code() + " - " + errorBody);
            }

            ResponseBody responseBody = response.body();
            if (responseBody == null) return;

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(responseBody.byteStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.startsWith("data: ")) {
                        String data = line.substring(6).trim();
                        try {
                            JsonNode node = objectMapper.readTree(data);
                            String type = node.path("type").asText();
                            if ("chunk".equals(type)) {
                                chunkConsumer.accept(node.path("content").asText());
                            }
                            // done 和 error 由上层处理
                        } catch (Exception e) {
                            log.debug("解析 SSE 数据失败: {}", e.getMessage());
                        }
                    }
                }
            }
        }
    }

    /**
     * 调用 Agent 流式规划（SSE 进度推送）
     * POST /agent/plan/stream
     *
     * @param progressConsumer 进度消息回调
     * @param resultConsumer   最终结果回调（JsonNode）
     */
    public void planStream(String city, Double budget, Integer days, String sessionId,
                           Consumer<String> progressConsumer,
                           Consumer<JsonNode> resultConsumer) throws IOException {
        Map<String, Object> body = new HashMap<>();
        body.put("city", city);
        body.put("budget", budget);
        body.put("days", days);
        if (sessionId != null) {
            body.put("session_id", sessionId);
        }

        String json = objectMapper.writeValueAsString(body);
        Request request = new Request.Builder()
                .url(agentBaseUrl + "/agent/plan/stream")
                .post(RequestBody.create(json, MediaType.parse("application/json")))
                .header("Accept", "text/event-stream")
                .build();

        log.debug("Agent 流式规划请求: {}", json);

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String errorBody = response.body() != null ? response.body().string() : "";
                throw new IOException("Agent 流式规划失败: HTTP " + response.code() + " - " + errorBody);
            }

            ResponseBody responseBody = response.body();
            if (responseBody == null) return;

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(responseBody.byteStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    String dataStr = null;
                    if (line.startsWith("data: ")) {
                        dataStr = line.substring(6).trim();
                    } else if (line.startsWith("data:")) {
                        dataStr = line.substring(5).trim();
                    }
                    if (dataStr == null || dataStr.isEmpty()) continue;

                    try {
                        JsonNode node = objectMapper.readTree(dataStr);
                        String type = node.path("type").asText();
                        if ("progress".equals(type)) {
                            String message = node.path("message").asText();
                            if (!message.isEmpty()) {
                                progressConsumer.accept(message);
                            }
                        } else if ("result".equals(type)) {
                            JsonNode data = node.path("data");
                            resultConsumer.accept(data);
                        } else if ("error".equals(type)) {
                            throw new IOException(node.path("message").asText("Agent 规划失败"));
                        }
                    } catch (IOException e) {
                        throw e;
                    } catch (Exception e) {
                        log.debug("解析 SSE 数据失败: {}", e.getMessage());
                    }
                }
            }
        }
    }

    /**
     * 健康检查
     */
    public boolean healthCheck() {
        try {
            Request request = new Request.Builder()
                    .url(agentBaseUrl + "/health")
                    .get()
                    .build();

            try (Response response = httpClient.newCall(request).execute()) {
                return response.isSuccessful();
            }
        } catch (Exception e) {
            log.warn("Agent 服务不可用: {}", e.getMessage());
            return false;
        }
    }
}
