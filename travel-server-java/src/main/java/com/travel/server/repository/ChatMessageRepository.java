package com.travel.server.repository;

import com.travel.server.entity.ChatMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, Long> {

    List<ChatMessage> findByUserIdAndSessionIdOrderByCreatedAtAsc(Long userId, String sessionId);

    @Query("SELECT m.sessionId FROM ChatMessage m WHERE m.userId = :userId GROUP BY m.sessionId ORDER BY MAX(m.createdAt) DESC")
    List<String> findDistinctSessionIdsByUserId(@Param("userId") Long userId);

    @Modifying
    @Transactional
    @Query("DELETE FROM ChatMessage m WHERE m.createdAt < :before")
    void deleteByCreatedAtBefore(@Param("before") LocalDateTime before);

    @Modifying
    @Transactional
    @Query("DELETE FROM ChatMessage m WHERE m.userId = :userId AND m.sessionId = :sessionId")
    void deleteByUserIdAndSessionId(@Param("userId") Long userId, @Param("sessionId") String sessionId);
}
