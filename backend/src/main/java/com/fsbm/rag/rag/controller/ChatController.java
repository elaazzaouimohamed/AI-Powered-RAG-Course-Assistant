package com.fsbm.rag.rag.controller;

import com.fsbm.rag.rag.dto.ChatRequest;
import com.fsbm.rag.rag.service.LlmProviderService;
import com.fsbm.rag.rag.service.PromptBuilderService;
import com.fsbm.rag.rag.service.RetrievalService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

/**
 * Endpoint principal du chat RAG avec streaming SSE.
 *
 * <p>Flux d'une requête :
 * <ol>
 *   <li>Réception de la question ({@code ChatRequest})</li>
 *   <li>Recherche vectorielle → {@code RetrievalService}</li>
 *   <li>Construction du prompt → {@code PromptBuilderService}</li>
 *   <li>Inférence en streaming → {@code LlmProviderService}</li>
 *   <li>Retour SSE ({@code text/event-stream}) vers le frontend</li>
 * </ol>
 * </p>
 */
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

    private final RetrievalService retrievalService;
    private final PromptBuilderService promptBuilderService;
    private final LlmProviderService llmProviderService;

    /**
     * Lance une session de chat et retourne la réponse en streaming SSE.
     *
     * <p>POST /api/chat/stream</p>
     * <p>Produit : {@code text/event-stream}</p>
     *
     * @param request corps JSON de la requête
     * @param userId  identifiant de l'utilisateur authentifié (injecté par Spring Security)
     * @return flux SSE de fragments {@code ChatResponse}
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> streamChat(
            @Valid @RequestBody ChatRequest request,
            @AuthenticationPrincipal Long userId) {
        // TODO: orchestrer retrieval → promptBuilder → llmProvider
        // TODO: mapper chaque token en ChatResponse JSON et l'émettre comme événement SSE
        throw new UnsupportedOperationException("streamChat non implémenté");
    }
}
