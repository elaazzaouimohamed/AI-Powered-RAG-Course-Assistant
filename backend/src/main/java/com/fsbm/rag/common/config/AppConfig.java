package com.fsbm.rag.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

/**
 * Configuration générale de l'application : clients HTTP, beans utilitaires.
 */
@Configuration
public class AppConfig {

    /**
     * Client HTTP réactif pour les appels vers les providers LLM et le service Python.
     *
     * @return instance de {@code WebClient.Builder} préconfigurée
     */
    @Bean
    public WebClient.Builder webClientBuilder() {
        // TODO: configurer les timeouts, les codecs (taille max des réponses LLM)
        return WebClient.builder();
    }
}
