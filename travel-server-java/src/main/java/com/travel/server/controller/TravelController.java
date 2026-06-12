package com.travel.server.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.travel.server.dto.ChatRequestDTO;
import com.travel.server.dto.TravelRequestDTO;
import com.travel.server.entity.ChatMessage;
import com.travel.server.repository.ChatMessageRepository;
import com.travel.server.service.TravelService;
import com.travel.server.vo.*;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import jakarta.annotation.PreDestroy;

/**
 * 旅游推荐 API 控制器
 */
@RestController
@RequestMapping("/api/travel")
public class TravelController {

    private static final Logger log = LoggerFactory.getLogger(TravelController.class);

    private final TravelService travelService;
    private final ObjectMapper objectMapper;
    private final ChatMessageRepository chatMessageRepository;
    private final ExecutorService chatExecutor = Executors.newFixedThreadPool(10);

    public TravelController(TravelService travelService, ObjectMapper objectMapper,
                            ChatMessageRepository chatMessageRepository) {
        this.travelService = travelService;
        this.objectMapper = objectMapper;
        this.chatMessageRepository = chatMessageRepository;
    }

    /**
     * 智能旅游规划（非流式）
     */
    @PostMapping("/recommend")
    public Result<TravelRecommendVO> recommend(@Valid @RequestBody TravelRequestDTO request) {
        log.info("收到旅游规划请求: city={}, budget={}, days={}",
                request.getCity(), request.getBudget(), request.getDays());

        TravelRecommendVO result = travelService.recommend(
                request.getCity(), request.getBudget(), request.getDays());

        if (Boolean.TRUE.equals(result.getSuccess())) {
            return Result.ok(result);
        } else {
            return Result.fail(500, result.getError());
        }
    }

    /**
     * 智能旅游规划（流式 SSE）
     * 前端可实时看到规划进度
     */
    @PostMapping(value = "/recommend/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter recommendStream(@Valid @RequestBody TravelRequestDTO request) {
        log.info("收到流式旅游规划请求: city={}, budget={}, days={}",
                request.getCity(), request.getBudget(), request.getDays());

        SseEmitter emitter = new SseEmitter(180_000L);

        chatExecutor.execute(() -> {
            try {
                travelService.recommendStream(
                        request.getCity(), request.getBudget(), request.getDays(),
                        progressMessage -> {
                            try {
                                StreamChunkVO progress = new StreamChunkVO(progressMessage);
                                progress.setType("progress");
                                emitter.send(SseEmitter.event()
                                        .name("message")
                                        .data(objectMapper.writeValueAsString(progress)));
                            } catch (IOException e) {
                                log.error("SSE 发送进度失败", e);
                            }
                        },
                        result -> {
                            try {
                                StreamResultVO resultEvent = new StreamResultVO(result);
                                emitter.send(SseEmitter.event()
                                        .name("message")
                                        .data(objectMapper.writeValueAsString(resultEvent)));
                                emitter.complete();
                            } catch (IOException e) {
                                log.error("SSE 发送结果失败", e);
                                emitter.completeWithError(e);
                            }
                        }
                );
            } catch (IOException e) {
                log.error("流式规划调用失败", e);
                try {
                    StreamErrorVO error = new StreamErrorVO("AI 服务暂时不可用: " + e.getMessage());
                    emitter.send(SseEmitter.event()
                            .name("message")
                            .data(objectMapper.writeValueAsString(error)));
                } catch (IOException ex) {
                    log.error("SSE 发送错误信息失败", ex);
                }
                emitter.completeWithError(e);
            }
        });

        emitter.onTimeout(emitter::complete);

        return emitter;
    }

    /**
     * AI 对话（SSE 流式）
     */
    @PostMapping(value = "/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chat(@Valid @RequestBody ChatRequestDTO request) {
        log.info("收到对话请求: message={}", request.getMessage());

        SseEmitter emitter = new SseEmitter(180_000L); // 180 秒超时

        // 在主线程中获取 userId，避免 executor 线程中 SecurityContext 丢失
        final Long userId = ChatHistoryController.getCurrentUserId();

        chatExecutor.execute(() -> {
            // 保存用户消息
            ChatMessage userMsg = new ChatMessage();
            userMsg.setUserId(userId);
            userMsg.setSessionId(request.getSessionId());
            userMsg.setRole("user");
            userMsg.setContent(request.getMessage());
            chatMessageRepository.save(userMsg);

            // 用于收集 AI 流式回复的完整内容
            StringBuilder aiContent = new StringBuilder();

            try {
                travelService.chat(request.getMessage(), request.getSessionId(), content -> {
                    try {
                        aiContent.append(content);
                        StreamChunkVO chunk = new StreamChunkVO(content);
                        emitter.send(SseEmitter.event()
                                .name("message")
                                .data(objectMapper.writeValueAsString(chunk)));
                    } catch (IOException e) {
                        log.error("SSE 发送数据失败", e);
                    }
                });

                // 保存 AI 完整回复
                if (aiContent.length() > 0) {
                    ChatMessage aiMsg = new ChatMessage();
                    aiMsg.setUserId(userId);
                    aiMsg.setSessionId(request.getSessionId());
                    aiMsg.setRole("ai");
                    aiMsg.setContent(aiContent.toString());
                    chatMessageRepository.save(aiMsg);
                }

                // 发送完成信号
                StreamDoneVO done = new StreamDoneVO();
                emitter.send(SseEmitter.event()
                        .name("message")
                        .data(objectMapper.writeValueAsString(done)));
                emitter.complete();

            } catch (IOException e) {
                log.error("对话流式调用失败", e);
                try {
                    StreamErrorVO error = new StreamErrorVO("AI 服务暂时不可用: " + e.getMessage());
                    emitter.send(SseEmitter.event()
                            .name("message")
                            .data(objectMapper.writeValueAsString(error)));
                } catch (IOException ex) {
                    log.error("SSE 发送错误信息失败", ex);
                }
                emitter.completeWithError(e);
            }
        });

        emitter.onTimeout(emitter::complete);

        return emitter;
    }

    /**
     * 关闭线程池
     */
    @PreDestroy
    public void destroy() {
        chatExecutor.shutdown();
        try {
            if (!chatExecutor.awaitTermination(10, TimeUnit.SECONDS)) {
                chatExecutor.shutdownNow();
            }
        } catch (InterruptedException e) {
            chatExecutor.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}
