package com.rag.app.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

/**
 * Pool de threads borné et géré par Spring pour le streaming SSE des réponses LLM.
 * Remplace un Executors.newCachedThreadPool() non borné et jamais fermé.
 */
@Configuration
public class AsyncConfig {

    @Bean(name = "sseExecutor", destroyMethod = "shutdown")
    public ThreadPoolTaskExecutor sseExecutor() {
        var executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(50);
        executor.setThreadNamePrefix("sse-llm-");
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(30);
        executor.initialize();
        return executor;
    }
}
