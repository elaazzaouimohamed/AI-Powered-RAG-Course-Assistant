package com.rag.app.model;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "llm_configs")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LlmConfig {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;          // "LM Studio — gemma3:4b"

    @Column(nullable = false)
    private String backend;       // nvidia | ollama | lmstudio

    @Column(nullable = false)
    private String model;         // gemma3:4b

    private String baseUrl;       // null = valeur par défaut de application.properties

    @Column(length = 1024)
    private String apiKey;        // uniquement pour nvidia

    @Builder.Default
    @Column(nullable = false)
    private Double temperature = 0.3;   // créativité de la génération (0.0 - 1.0)

    @Builder.Default
    @Column(nullable = false)
    private Integer maxTokens = 2048;   // longueur max de la réponse

    @Builder.Default
    private boolean enabled = true;

    @Builder.Default
    private boolean isDefault = false;
}
