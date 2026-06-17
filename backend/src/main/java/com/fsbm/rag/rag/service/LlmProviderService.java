package com.fsbm.rag.rag.service;

import reactor.core.publisher.Flux;

/**
 * Interface clé du système RAG : abstraction du provider LLM.
 *
 * <p>Trois implémentations concrètes existent : {@code OllamaProvider},
 * {@code VllmProvider} et {@code CloudApiProvider}. Le choix est piloté par
 * la propriété {@code llm.provider} dans {@code application.yml}.</p>
 *
 * <p>Le retour en {@link Flux} permet un streaming SSE direct vers le client
 * sans tamponner la réponse complète en mémoire.</p>
 */
public interface LlmProviderService {

    /**
     * Envoie un prompt au LLM et retourne un flux de tokens au fil de leur génération.
     *
     * @param prompt prompt complet (contexte RAG + question) déjà formaté
     * @return flux réactif de fragments de texte
     */
    Flux<String> streamCompletion(String prompt);

    /**
     * Vérifie que le provider est accessible (health check).
     *
     * @return {@code true} si le LLM répond aux requêtes
     */
    boolean isAvailable();
}
