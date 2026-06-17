package com.fsbm.rag.rag.provider;

import com.fsbm.rag.rag.service.LlmProviderService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

/**
 * Provider LLM via API cloud (OpenAI, Anthropic, Mistral AI…).
 *
 * <p>Activé quand {@code llm.provider=cloud}. Fallback utile lors de la démo
 * si l'infrastructure locale n'est pas disponible. La base-url est configurable
 * ({@code llm.cloud.base-url}) pour pointer vers n'importe quelle API compatible.</p>
 */
@Service
@ConditionalOnProperty(name = "llm.provider", havingValue = "cloud")
public class CloudApiProvider implements LlmProviderService {

    /**
     * Appelle l'API cloud en mode streaming.
     *
     * @param prompt prompt complet formaté par {@code PromptBuilderService}
     * @return flux réactif de fragments
     */
    @Override
    public Flux<String> streamCompletion(String prompt) {
        // TODO: appel HTTP avec l'API key depuis la config
        // TODO: gérer la désérialisation SSE selon le format du provider (OpenAI / Anthropic)
        throw new UnsupportedOperationException("CloudApiProvider.streamCompletion non implémenté");
    }

    /** {@inheritDoc} */
    @Override
    public boolean isAvailable() {
        // TODO: tentative de ping sur l'endpoint configuré
        throw new UnsupportedOperationException("CloudApiProvider.isAvailable non implémenté");
    }
}
