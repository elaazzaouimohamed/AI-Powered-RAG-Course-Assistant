package com.fsbm.rag.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;

import java.time.Duration;

/**
 * Configuration du cache Redis.
 *
 * <p>Utilisé pour mettre en cache les résultats de recherche vectorielle fréquents
 * et les sessions de chat (TTL configurable par type de donnée).</p>
 */
@Configuration
public class RedisConfig {

    /**
     * Gestionnaire de cache Redis avec sérialisation JSON et TTL par défaut de 10 minutes.
     *
     * @param factory fabrique de connexions Redis (auto-configurée par Spring Boot)
     * @return gestionnaire de cache configuré
     */
    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(10))
                .serializeValuesWith(
                        RedisSerializationContext.SerializationPair.fromSerializer(
                                new GenericJackson2JsonRedisSerializer()
                        )
                );

        // TODO: déclarer des caches nommés avec des TTL spécifiques (ex: "retrieval" → 5min)
        return RedisCacheManager.builder(factory)
                .cacheDefaults(config)
                .build();
    }
}
