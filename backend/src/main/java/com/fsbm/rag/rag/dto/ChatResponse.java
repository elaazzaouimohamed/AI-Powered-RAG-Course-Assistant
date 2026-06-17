package com.fsbm.rag.rag.dto;

import java.util.List;

/**
 * Représentation d'un fragment de réponse généré par le LLM.
 *
 * <p>En mode streaming SSE, plusieurs {@code ChatResponse} sont envoyés successivement.
 * Le dernier fragment a {@code done = true} et peut inclure les sources utilisées.</p>
 *
 * @param delta     fragment de texte courant (peut être vide pour le dernier message)
 * @param done      {@code true} si c'est le dernier fragment du stream
 * @param sources   liste des sources (titres de documents) utilisées pour la réponse — uniquement dans le dernier fragment
 * @param sessionId identifiant de session, renvoyé pour permettre la continuation du contexte
 */
public record ChatResponse(
    String delta,
    boolean done,
    List<String> sources,
    String sessionId
) {}
