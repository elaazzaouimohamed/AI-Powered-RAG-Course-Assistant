package com.fsbm.rag.auth.service;

import com.fsbm.rag.auth.model.User;

/**
 * Service d'authentification et d'inscription.
 *
 * <p>Orchestre la validation des credentials, le hachage des mots de passe
 * et l'émission des tokens JWT via {@code JwtTokenProvider}.</p>
 */
public interface AuthService {

    /**
     * Authentifie un utilisateur et retourne un token JWT.
     *
     * @param email    adresse e-mail
     * @param password mot de passe en clair
     * @return token JWT signé
     * @throws com.fsbm.rag.common.exception.UnauthorizedException si les credentials sont invalides
     */
    String login(String email, String password);

    /**
     * Inscrit un nouvel utilisateur avec le rôle STUDENT par défaut.
     *
     * @param fullName nom complet
     * @param email    adresse e-mail (doit être unique)
     * @param password mot de passe en clair (sera haché)
     * @return l'entité utilisateur créée
     * @throws com.fsbm.rag.common.exception.ConflictException si l'e-mail est déjà utilisé
     */
    User register(String fullName, String email, String password);

    /**
     * Charge un utilisateur par son e-mail pour Spring Security.
     *
     * @param email adresse e-mail
     * @return l'entité utilisateur
     */
    User loadUserByEmail(String email);
}
