package com.rag.app.repository;

import com.rag.app.model.Message;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface MessageRepository extends JpaRepository<Message, Long> {
    List<Message> findByConversationIdOrderByCreatedAtAsc(Long conversationId);
    long countByConversationUserId(Long userId);
    List<Message> findByConversationIdAndIdGreaterThan(Long conversationId, Long id);
}
