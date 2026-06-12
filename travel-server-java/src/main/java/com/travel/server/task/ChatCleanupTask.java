package com.travel.server.task;

import com.travel.server.repository.ChatMessageRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class ChatCleanupTask {

    private static final Logger log = LoggerFactory.getLogger(ChatCleanupTask.class);
    private final ChatMessageRepository chatMessageRepository;

    public ChatCleanupTask(ChatMessageRepository chatMessageRepository) {
        this.chatMessageRepository = chatMessageRepository;
    }

    /** 每天凌晨 3 点清理超过 3 天的对话消息 */
    @Scheduled(cron = "0 0 3 * * ?")
    public void cleanOldMessages() {
        LocalDateTime threeDaysAgo = LocalDateTime.now().minusDays(3);
        chatMessageRepository.deleteByCreatedAtBefore(threeDaysAgo);
        log.info("已清理 {} 之前的对话记录", threeDaysAgo);
    }
}
