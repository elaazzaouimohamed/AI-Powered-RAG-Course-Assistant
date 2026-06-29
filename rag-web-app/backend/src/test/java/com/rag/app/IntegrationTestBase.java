package com.rag.app;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Base des tests d'intégration : démarre le contexte Spring complet sur une base H2,
 * avec la vraie chaîne de filtres de sécurité. DataInitializer amorce admin/demo.
 */
@SpringBootTest
@AutoConfigureMockMvc
public abstract class IntegrationTestBase {

    @Autowired protected MockMvc mvc;
    @Autowired protected ObjectMapper om;

    protected String json(Object o) throws Exception {
        return om.writeValueAsString(o);
    }

    /** Authentifie un utilisateur amorcé et renvoie son jeton d'accès. */
    protected String tokenFor(String username, String password) throws Exception {
        MvcResult res = mvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("username", username, "password", password))))
                .andExpect(status().isOk())
                .andReturn();
        return om.readTree(res.getResponse().getContentAsString()).get("accessToken").asText();
    }

    protected String adminToken() throws Exception { return tokenFor("admin", "admin123"); }
    protected String demoToken()  throws Exception { return tokenFor("demo", "demo123"); }
}
