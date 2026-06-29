package com.rag.app;

import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;

import java.util.Map;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/** Tests d'intégration de l'API d'authentification (login, register, refresh, /me). */
class AuthApiIntegrationTest extends IntegrationTestBase {

    @Test
    void loginWithSeededAdminReturnsTokens() throws Exception {
        mvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", "admin", "password", "admin123"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.refreshToken").isNotEmpty())
                .andExpect(jsonPath("$.role").value("ADMIN"));
    }

    @Test
    void loginWithWrongPasswordReturns401() throws Exception {
        mvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", "admin", "password", "WRONG"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void registerCreatesUserAndReturnsTokens() throws Exception {
        String username = "user_" + UUID.randomUUID().toString().substring(0, 8);
        mvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", username,
                                "email", username + "@x.com", "password", "secret123"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.role").value("USER"));
    }

    @Test
    void registerWithDuplicateUsernameReturns400() throws Exception {
        mvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", "admin",
                                "email", "other@x.com", "password", "secret123"))))
                .andExpect(status().isBadRequest());
    }

    @Test
    void refreshWithValidTokenReturnsNewTokens() throws Exception {
        // Récupère un refresh token valide via login
        MvcResult login = mvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", "demo", "password", "demo123"))))
                .andExpect(status().isOk()).andReturn();
        JsonNode body = om.readTree(login.getResponse().getContentAsString());
        String refresh = body.get("refreshToken").asText();

        // Le refresh ne doit PAS planter (régression du ClassCastException corrigé)
        mvc.perform(post("/api/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("refreshToken", refresh))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").isNotEmpty())
                .andExpect(jsonPath("$.role").value("USER"));
    }

    @Test
    void refreshWithInvalidTokenReturns400() throws Exception {
        mvc.perform(post("/api/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("refreshToken", "garbage.token.value"))))
                .andExpect(status().isBadRequest());
    }

    @Test
    void meEndpointRequiresAuthentication() throws Exception {
        mvc.perform(get("/api/auth/me"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void meEndpointWithTokenReturnsProfile() throws Exception {
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + adminToken()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("admin"));
    }
}
