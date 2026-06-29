package com.rag.app.dto.chat;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ChatRequest {
    @NotBlank private String question;
    private String course;       // optionnel : stem du JSON (ex: Statistique_cours). Vide = réponse sans contexte RAG.
    private String backend;      // optionnel : nvidia | ollama | lmstudio (défaut lmstudio)
    private String model;        // null = modèle par défaut du backend
    private Double temperature;  // optionnel : surcharge la température de la config (0..1)
}
