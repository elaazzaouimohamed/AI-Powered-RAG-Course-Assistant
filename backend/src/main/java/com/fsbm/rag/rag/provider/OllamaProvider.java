package com.fsbm.rag.rag.provider;

import com.fsbm.rag.rag.service.LlmProviderService;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

/**
 * Provider LLM utilisant Ollama (inférence locale).
 *
 * <p>Activé quand {@code llm.provider=ollama} dans {@code application.yml}.
 * Communique avec l'API HTTP d'Ollama ({@code /api/generate}) en mode streaming.</p>
 */
@Service
@ConditionalOnProperty(name = "llm.provider", havingValue = "ollama")
public class OllamaProvider implements LlmProviderService {

    /**
     * Envoie le prompt à Ollama via son endpoint HTTP et streame les tokens retournés.
     *
     * @param prompt prompt complet formaté par {@code PromptBuilderService}
     * @return flux réactif de fragments de texte
     */
    @Override
    public Flux<String> streamCompletion(String prompt) {
        // TODO: appeler POST http://localhost:11434/api/generate avec WebClient
        // TODO: désérialiser le stream NDJSON et extraire le champ "response"
        throw new UnsupportedOperationException("OllamaProvider.streamCompletion non implémenté");
    }

    /** {@inheritDoc} */
    @Override
    public boolean isAvailable() {
        // TODO: GET /api/tags pour vérifier que le modèle configuré est chargé
        throw new UnsupportedOperationException("OllamaProvider.isAvailable non implémenté");
    }
}
