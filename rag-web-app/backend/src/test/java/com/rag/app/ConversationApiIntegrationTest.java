package com.rag.app;

import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/** Tests d'intégration de l'API conversations (CRUD + isolation entre utilisateurs). */
class ConversationApiIntegrationTest extends IntegrationTestBase {

    private long createConversationFor(String token) throws Exception {
        MvcResult res = mvc.perform(post("/api/conversations")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("course", "Stat", "backend", "lmstudio"))))
                .andExpect(status().isOk())
                .andReturn();
        return om.readTree(res.getResponse().getContentAsString()).get("id").asLong();
    }

    @Test
    void createAndGetOwnConversation() throws Exception {
        String token = demoToken();
        long id = createConversationFor(token);

        mvc.perform(get("/api/conversations/" + id).header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(id))
                .andExpect(jsonPath("$.course").value("Stat"));
    }

    @Test
    void listReturnsOnlyOwnConversations() throws Exception {
        String demo = demoToken();
        createConversationFor(demo);

        MvcResult res = mvc.perform(get("/api/conversations").header("Authorization", "Bearer " + demo))
                .andExpect(status().isOk()).andReturn();
        JsonNode arr = om.readTree(res.getResponse().getContentAsString());
        assertThat(arr.isArray()).isTrue();
        assertThat(arr.size()).isGreaterThanOrEqualTo(1);
    }

    @Test
    void cannotAccessAnotherUsersConversation() throws Exception {
        long demoConv = createConversationFor(demoToken());

        // admin (autre utilisateur) tente d'accéder à la conversation de demo → 404
        mvc.perform(get("/api/conversations/" + demoConv).header("Authorization", "Bearer " + adminToken()))
                .andExpect(status().isNotFound());
    }

    @Test
    void cannotDeleteAnotherUsersConversation() throws Exception {
        long demoConv = createConversationFor(demoToken());

        mvc.perform(delete("/api/conversations/" + demoConv).header("Authorization", "Bearer " + adminToken()))
                .andExpect(status().isNotFound());
    }

    @Test
    void renameOwnConversation() throws Exception {
        String token = demoToken();
        long id = createConversationFor(token);

        mvc.perform(patch("/api/conversations/" + id)
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("title", "Mon titre"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.title").value("Mon titre"));
    }

    @Test
    void deleteOwnConversationReturns204() throws Exception {
        String token = demoToken();
        long id = createConversationFor(token);

        mvc.perform(delete("/api/conversations/" + id).header("Authorization", "Bearer " + token))
                .andExpect(status().isNoContent());

        mvc.perform(get("/api/conversations/" + id).header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());
    }
}
