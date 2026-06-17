package com.fsbm.rag.auth.controller;

import com.fsbm.rag.auth.service.AuthService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * Endpoints d'authentification : connexion et inscription.
 *
 * <p>Toutes les routes de ce contrôleur sont publiques (configurées dans
 * {@code SecurityConfig} comme {@code /api/auth/**}).</p>
 */
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * Connecte un utilisateur et retourne un token JWT.
     *
     * <p>POST /api/auth/login</p>
     *
     * @param request corps JSON contenant {@code email} et {@code password}
     * @return {@code 200 OK} avec {@code { "token": "..." }}
     */
    @PostMapping("/login")
    public ResponseEntity<?> login(@Valid @RequestBody LoginRequest request) {
        // TODO: déléguer à authService.login(), retourner le token dans un TokenResponse
        throw new UnsupportedOperationException("login non implémenté");
    }

    /**
     * Inscrit un nouvel étudiant.
     *
     * <p>POST /api/auth/register</p>
     *
     * @param request corps JSON contenant {@code fullName}, {@code email} et {@code password}
     * @return {@code 201 Created} avec les données de l'utilisateur créé
     */
    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody RegisterRequest request) {
        // TODO: déléguer à authService.register(), retourner 201 avec UserResponse
        throw new UnsupportedOperationException("register non implémenté");
    }

    // ── DTOs internes (records Java 17) ─────────────────────────────────────

    record LoginRequest(
        @Email @NotBlank String email,
        @NotBlank String password
    ) {}

    record RegisterRequest(
        @NotBlank String fullName,
        @Email @NotBlank String email,
        @NotBlank String password
    ) {}
}
