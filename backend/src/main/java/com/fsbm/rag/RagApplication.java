package com.fsbm.rag;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Point d'entrée principal de l'application RAG Explicateur.
 *
 * <p>L'application est structurée comme un monolithe modulaire dont les packages
 * ({@code auth}, {@code rag}, {@code ingestion}, {@code quiz}) peuvent être extraits
 * en microservices indépendants lors d'une montée en charge vers un déploiement
 * universitaire.</p>
 */
@SpringBootApplication
@EnableCaching
@EnableAsync
public class RagApplication {

    public static void main(String[] args) {
        SpringApplication.run(RagApplication.class, args);
    }
}
