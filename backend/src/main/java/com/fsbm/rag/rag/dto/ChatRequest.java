package com.fsbm.rag.rag.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * Corps de la requête envoyée par le frontend pour une session de chat.
 *
 * @param question     question posée par l'étudiant (max 2 000 caractères)
 * @param courseId     identifiant du cours ciblé pour la recherche vectorielle (optionnel)
 * @param sessionId    identifiant de session pour conserver le contexte conversationnel (optionnel)
 * @param topK         nombre de chunks à récupérer dans pgvector (défaut : 5)
 */
public record ChatRequest(

    @NotBlank
    @Size(max = 2000)
    String question,

    Long courseId,

    String sessionId,

    Integer topK
) {
    /** Valeur par défaut de topK si non fournie par le client. */
    public int topKOrDefault() {
        return topK != null ? topK : 5;
    }
}
