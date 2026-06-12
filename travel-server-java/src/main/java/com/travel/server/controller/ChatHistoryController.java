package com.travel.server.controller;

import com.travel.server.entity.ChatMessage;
import com.travel.server.repository.ChatMessageRepository;
import com.travel.server.vo.Result;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/chat")
public class ChatHistoryController {

    private final ChatMessageRepository chatMessageRepository;

    public ChatHistoryController(ChatMessageRepository chatMessageRepository) {
        this.chatMessageRepository = chatMessageRepository;
    }

    /** 获取当前用户的对话会话列表 */
    @GetMapping("/sessions")
    public Result<?> getSessions() {
        Long userId = getCurrentUserId();
        List<String> sessionIds = chatMessageRepository.findDistinctSessionIdsByUserId(userId);
        return Result.ok(sessionIds.stream().map(sid -> {
            List<ChatMessage> msgs = chatMessageRepository
                    .findByUserIdAndSessionIdOrderByCreatedAtAsc(userId, sid);
            ChatMessage last = msgs.isEmpty() ? null : msgs.get(msgs.size() - 1);
            return Map.of(
                    "sessionId", sid,
                    "messageCount", msgs.size(),
                    "lastMessage", last != null ? last.getContent().substring(0, Math.min(50, last.getContent().length())) : "",
                    "lastTime", last != null ? last.getCreatedAt().toString() : ""
            );
        }).toList());
    }

    /** 获取某个会话的全部消息 */
    @GetMapping("/sessions/{sessionId}/messages")
    public Result<?> getMessages(@PathVariable String sessionId) {
        Long userId = getCurrentUserId();
        List<ChatMessage> messages = chatMessageRepository
                .findByUserIdAndSessionIdOrderByCreatedAtAsc(userId, sessionId);
        return Result.ok(messages);
    }

    /** 删除某个会话的全部消息 */
    @DeleteMapping("/sessions/{sessionId}")
    public Result<?> deleteSession(@PathVariable String sessionId) {
        Long userId = getCurrentUserId();
        chatMessageRepository.deleteByUserIdAndSessionId(userId, sessionId);
        return Result.ok(Map.of("message", "已删除"));
    }

    /** 从 SecurityContext 获取当前用户 ID */
    static Long getCurrentUserId() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof Long) return (Long) principal;
        return Long.parseLong(principal.toString());
    }
}
