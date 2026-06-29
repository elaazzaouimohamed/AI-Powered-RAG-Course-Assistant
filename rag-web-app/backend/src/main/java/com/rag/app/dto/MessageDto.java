package com.rag.app.dto;

import lombok.Builder;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Builder
public class MessageDto {
    private Long id;
    private String role;
    private String content;
    private LocalDateTime createdAt;
}
