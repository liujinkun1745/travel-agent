package com.travel.server.utils;

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
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 大模型调用工具类
 */
@Component
public class LLMUtils {

    private static final Logger log = LoggerFactory.getLogger(LLMUtils.class);

    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;

    @Value("${llm.provider:siliconflow}")
    private String provider;

    @Value("${llm.deepseek.model:deepseek-chat}")
    private String deepseekModel;

    @Value("${llm.siliconflow.model:deepseek-ai/DeepSeek-V3}")
    private String siliconflowModel;

    public LLMUtils(ObjectMapper objectMapper,
                    @Value("${llm.connect-timeout:30}") int connectTimeout,
                    @Value("${llm.read-timeout:180}") int readTimeout,
                    @Value("${llm.write-timeout:30}") int writeTimeout) {
        this.objectMapper = objectMapper;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(connectTimeout, TimeUnit.SECONDS)
                .readTimeout(readTimeout, TimeUnit.SECONDS)
                .writeTimeout(writeTimeout, TimeUnit.SECONDS)
                .build();
    }

    /**
     * 获取当前提供商的 API Key
     */
    private String getApiKey() throws IOException {
        String key = System.getenv(provider.equals("siliconflow") ? "SILICONFLOW_API_KEY" : "DEEPSEEK_API_KEY");
        if (key == null || key.isEmpty() || key.startsWith("your-")) {
            String envName = provider.equals("siliconflow") ? "SILICONFLOW_API_KEY" : "DEEPSEEK_API_KEY";
            throw new IOException("未设置环境变量 " + envName
                    + "，请在系统环境变量中配置后再调用大模型 API");
        }
        return key;
    }

    /**
     * 非流式调用大模型
     *
     * @param systemPrompt 系统提示词
     * @param userMessage  用户消息
     * @return 大模型返回的完整文本
     */
    public String chat(String systemPrompt, String userMessage) throws IOException {
        Map<String, Object> requestBody = buildRequestBody(systemPrompt, userMessage, false);
        String json = objectMapper.writeValueAsString(requestBody);

        Request request = buildRequest(json);
        log.debug("LLM 请求: {}", requestBody);

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String errorBody = response.body() != null ? response.body().string() : "";
                throw new IOException("LLM 调用失败, HTTP " + response.code() + ": " + errorBody);
            }
            String responseBody = response.body().string();
            log.debug("LLM 响应: {}", responseBody);
            return extractContent(responseBody);
        }
    }

    /**
     * 流式调用大模型
     *
     * @param systemPrompt 系统提示词
     * @param userMessage  用户消息
     * @param chunkConsumer 每个 chunk 的回调，传 null 表示流结束
     */
    public void chatStream(String systemPrompt, String userMessage, Consumer<String> chunkConsumer) throws IOException {
        Map<String, Object> requestBody = buildRequestBody(systemPrompt, userMessage, true);
        String json = objectMapper.writeValueAsString(requestBody);

        Request request = buildRequest(json);
        log.debug("LLM 流式请求: {}", requestBody);

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                String errorBody = response.body() != null ? response.body().string() : "";
                throw new IOException("LLM 流式调用失败, HTTP " + response.code() + ": " + errorBody);
            }

            ResponseBody body = response.body();
            if (body == null) {
                return;
            }

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(body.byteStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.startsWith("data: ")) {
                        String data = line.substring(6).trim();
                        if ("[DONE]".equalsIgnoreCase(data)) {
                            break;
                        }
                        String content = parseStreamContent(data);
                        if (content != null && !content.isEmpty()) {
                            chunkConsumer.accept(content);
                        }
                    }
                }
            }
        }
    }

    /**
     * 从 LLM 响应中提取 JSON 内容
     * 降级链: ```json ``` → ``` ``` → 原始 {...}
     */
    public String extractJson(String response) {
        if (response == null || response.isEmpty()) {
            return null;
        }

        // 方法1: 匹配 ```json ... ```
        String[] patterns = {
                "```json\\n([\\s\\S]*?)\\n```",
                "```\\n([\\s\\S]*?)\\n```"
        };

        for (String patternStr : patterns) {
            Pattern pattern = Pattern.compile(patternStr);
            Matcher matcher = pattern.matcher(response);
            if (matcher.find()) {
                return matcher.group(1);
            }
        }

        // 方法2: 找到最外层 {...}
        int start = response.indexOf('{');
        int end = response.lastIndexOf('}');
        if (start != -1 && end != -1 && end > start) {
            return response.substring(start, end + 1);
        }

        return null;
    }

    /**
     * 构建 LLM 请求体
     */
    private Map<String, Object> buildRequestBody(String systemPrompt, String userMessage, boolean stream) {
        Map<String, Object> body = new HashMap<>();

        // 根据 provider 选择模型（从配置文件读取）
        String model = "deepseek".equals(provider) ? deepseekModel : siliconflowModel;
        body.put("model", model);
        body.put("stream", stream);
        body.put("max_tokens", 4096);
        body.put("temperature", 0.7);

        // 构建消息
        java.util.List<Map<String, String>> messages = new java.util.ArrayList<>();
        Map<String, String> sysMsg = new HashMap<>();
        sysMsg.put("role", "system");
        sysMsg.put("content", systemPrompt);
        messages.add(sysMsg);

        Map<String, String> userMsg = new HashMap<>();
        userMsg.put("role", "user");
        userMsg.put("content", userMessage);
        messages.add(userMsg);

        body.put("messages", messages);
        return body;
    }

    /**
     * 构建 HTTP 请求
     */
    private Request buildRequest(String json) throws IOException {
        String apiKey = getApiKey();
        String baseUrl;
        if ("deepseek".equals(provider)) {
            baseUrl = "https://api.deepseek.com/chat/completions";
        } else {
            baseUrl = "https://api.siliconflow.cn/v1/chat/completions";
        }

        return new Request.Builder()
                .url(baseUrl)
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .post(RequestBody.create(json, MediaType.parse("application/json")))
                .build();
    }

    /**
     * 从非流式响应中提取 content
     */
    private String extractContent(String responseBody) throws IOException {
        JsonNode root = objectMapper.readTree(responseBody);
        JsonNode choices = root.path("choices");
        if (choices.isArray() && choices.size() > 0) {
            return choices.get(0).path("message").path("content").asText();
        }
        return "";
    }

    /**
     * 从流式 SSE data 中提取 delta.content
     * 返回 null 表示该 chunk 无内容或解析失败
     */
    private String parseStreamContent(String data) {
        try {
            JsonNode root = objectMapper.readTree(data);
            JsonNode choices = root.path("choices");
            if (choices.isArray() && choices.size() > 0) {
                JsonNode delta = choices.get(0).path("delta");
                return delta.path("content").asText(null);
            }
        } catch (Exception e) {
            log.debug("解析流式数据失败: {}", e.getMessage());
        }
        return null;
    }
}
