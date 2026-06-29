package com.rag.app;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** Tests d'intégration de la sécurité : 401 vs 403, rôles, endpoints publics, CORS preflight. */
class SecurityIntegrationTest extends IntegrationTestBase {

    @Test
    void protectedEndpointWithoutTokenReturns401NotConfusing403() throws Exception {
        // Régression : un token absent doit donner 401 (non authentifié), pas 403.
        mvc.perform(get("/api/conversations"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void protectedEndpointWithInvalidTokenReturns401() throws Exception {
        mvc.perform(get("/api/conversations").header("Authorization", "Bearer not.a.real.token"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void adminEndpointAsNormalUserReturns403() throws Exception {
        // Authentifié mais sans le rôle ADMIN → 403 (interdit), pas 401.
        mvc.perform(get("/api/admin/stats").header("Authorization", "Bearer " + demoToken()))
                .andExpect(status().isForbidden());
    }

    @Test
    void adminEndpointAsAdminReturns200() throws Exception {
        mvc.perform(get("/api/admin/stats").header("Authorization", "Bearer " + adminToken()))
                .andExpect(status().isOk());
    }

    @Test
    void publicAuthEndpointsAreAccessibleWithoutToken() throws Exception {
        // login est public ; un mauvais mot de passe donne 401 mais PAS 403 (donc l'endpoint est ouvert)
        mvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", "nobody", "password", "nope"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void healthEndpointIsPublic() throws Exception {
        mvc.perform(get("/actuator/health"))
                .andExpect(status().isOk());
    }

    @Test
    void corsPreflightIsPermitted() throws Exception {
        mvc.perform(options("/api/conversations")
                        .header("Origin", "http://localhost:5173")
                        .header("Access-Control-Request-Method", "GET"))
                .andExpect(status().isOk());
    }
}
