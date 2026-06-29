package com.rag.app.dto.admin;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class LlmConfigDto {
    private Long id;
    private String name;
    private String backend;
    private String model;
    private String baseUrl;
    private String apiKey;
    private Double temperature;
    private Integer maxTokens;
    private boolean enabled;

    // Sans @JsonProperty, le getter Lombok isDefault() serait sérialisé
    // par Jackson sous la clé "default" → la case "par défaut" ne se sauvegardait jamais.
    @JsonProperty("isDefault")
    private boolean isDefault;
}
