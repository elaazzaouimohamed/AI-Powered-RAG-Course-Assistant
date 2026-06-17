package com.fsbm.rag.auth.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Utilitaire de génération et validation des tokens JWT.
 *
 * <p>Utilise la bibliothèque JJWT. Le secret et la durée de vie sont injectés
 * depuis {@code application.yml} ({@code security.jwt.*}).</p>
 */
@Component
public class JwtTokenProvider {

    @Value("${security.jwt.secret}")
    private String jwtSecret;

    @Value("${security.jwt.expiration-ms}")
    private long expirationMs;

    /**
     * Génère un token JWT signé pour l'utilisateur authentifié.
     *
     * @param email    identifiant de l'utilisateur
     * @param role     rôle à embarquer dans les claims
     * @return token JWT signé en Base64Url
     */
    public String generateToken(String email, String role) {
        // TODO: construire le JWT avec JJWT (subject, claim "role", iat, exp)
        throw new UnsupportedOperationException("generateToken non implémenté");
    }

    /**
     * Extrait l'adresse e-mail (subject) d'un token valide.
     *
     * @param token token JWT à décoder
     * @return l'e-mail embarqué dans le subject
     */
    public String getEmailFromToken(String token) {
        // TODO: parser le JWT et retourner le subject
        throw new UnsupportedOperationException("getEmailFromToken non implémenté");
    }

    /**
     * Vérifie la signature et la date d'expiration du token.
     *
     * @param token token JWT à valider
     * @return {@code true} si le token est valide et non expiré
     */
    public boolean validateToken(String token) {
        // TODO: valider la signature HMAC et la date d'expiration
        throw new UnsupportedOperationException("validateToken non implémenté");
    }
}
