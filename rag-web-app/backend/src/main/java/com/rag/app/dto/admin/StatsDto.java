package com.rag.app.dto.admin;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class StatsDto {
    private long totalUsers;
    private long totalConversations;
    private long totalMessages;
    private long activeUsers;
    private long enabledLlms;
}
