package com.fsbm.rag.rag.provider;

import com.fsbm.rag.rag.service.LlmProviderService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

/**
 * Provider LLM utilisant vLLM (inférence GPU optimisée, compatible OpenAI API).
 *
 * <p>Activé quand {@code llm.provider=vllm}. L'API vLLM est compatible avec
 * l'API OpenAI, donc on cible {@code /v1/chat/completions} avec SSE activé
 * ({@code stream: true}).</p>
 */
@Service
@ConditionalOnProperty(name = "llm.provider", havingValue = "vllm")
public class VllmProvider implements LlmProviderService {

    /**
     * Appelle l'endpoint chat/completions de vLLM en mode streaming.
     *
     * @param prompt prompt complet formaté par {@code PromptBuilderService}
     * @return flux réactif de fragments text/event-stream
     */
    @Override
    public Flux<String> streamCompletion(String prompt) {
        // TODO: POST /v1/chat/completions avec { stream: true }
        // TODO: parser les lignes "data: {...}" du SSE et extraire delta.content
        throw new UnsupportedOperationException("VllmProvider.streamCompletion non implémenté");
    }

    /** {@inheritDoc} */
    @Override
    public boolean isAvailable() {
        // TODO: GET /health sur l'endpoint vLLM
        throw new UnsupportedOperationException("VllmProvider.isAvailable non implémenté");
    }
}
