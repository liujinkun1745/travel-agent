package com.travel.server.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * AI 对话请求
 */
public class ChatRequestDTO {

    @NotBlank(message = "消息不能为空")
    private String message;

    private String sessionId;

    public ChatRequestDTO() {}

    public ChatRequestDTO(String message) {
        this.message = message;
    }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    public String getSessionId() { return sessionId; }
    public void setSessionId(String sessionId) { this.sessionId = sessionId; }
}
