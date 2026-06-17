package com.fsbm.rag.auth.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Configuration centrale de Spring Security.
 *
 * <p>Stratégie stateless (JWT) — aucune session HTTP n'est créée côté serveur.
 * Le filtre JWT est injecté avant {@code UsernamePasswordAuthenticationFilter}.</p>
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    /**
     * Définit les règles d'accès, désactive CSRF (API REST stateless)
     * et enregistre le filtre JWT.
     *
     * @param http constructeur de la chaîne de filtres
     * @return la chaîne de filtres configurée
     */
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        // TODO: configurer les routes publiques (/api/auth/**) et sécurisées
        // TODO: injecter JwtAuthFilter avant UsernamePasswordAuthenticationFilter
        // TODO: configurer CORS pour le frontend React (localhost:5173 en dev)
        throw new UnsupportedOperationException("filterChain non implémenté");
    }

    /**
     * Encodeur de mot de passe BCrypt (force 12).
     *
     * @return instance de {@code BCryptPasswordEncoder}
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}
