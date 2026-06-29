package com.rag.app;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.request;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Tests d'intégration du flux de chat SSE. Vérifie le correctif clé : sur cet endpoint
 * text/event-stream, les erreurs (question vide, conversation non possédée) passent par
 * le canal SSE 'error' avec un statut 200, et NE dégénèrent PAS en 401 trompeur.
 *
 * Note : sseError() écrit l'événement de façon synchrone avant de rendre l'émetteur, donc
 * le corps est déjà présent dans la réponse — pas besoin d'asyncDispatch (qui re-déclencherait
 * la chaîne de sécurité sur le dispatch ASYNC, un artefact propre à MockMvc).
 */
class ChatApiIntegrationTest extends IntegrationTestBase {

    private long createConv(String token) throws Exception {
        MvcResult res = mvc.perform(post("/api/conversations")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(Map.of("course", "", "backend", "lmstudio"))))
                .andExpect(status().isOk()).andReturn();
        return om.readTree(res.getResponse().getContentAsString()).get("id").asLong();
    }

    private MvcResult startStream(String token, long convId, Map<String, Object> body) throws Exception {
        return mvc.perform(post("/api/conversations/" + convId + "/stream")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .accept(MediaType.parseMediaType("text/event-stream"))
                        .content(json(body)))
                .andExpect(request().asyncStarted())  // auth a réussi : on est entré dans le contrôleur
                .andReturn();
    }

    private Map<String, Object> body(String question) {
        Map<String, Object> b = new HashMap<>();
        b.put("question", question);
        b.put("course", "");
        b.put("backend", "lmstudio");
        return b;
    }

    @Test
    void streamWithoutTokenReturns401() throws Exception {
        mvc.perform(post("/api/conversations/1/stream")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(json(body("test"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void blankQuestionYieldsSseErrorNot401() throws Exception {
        String token = demoToken();
        long conv = createConv(token);

        MvcResult result = startStream(token, conv, body("   "));

        assertThat(result.getResponse().getStatus()).isEqualTo(200);
        assertThat(result.getResponse().getContentAsString(StandardCharsets.UTF_8))
                .contains("La question ne peut pas être vide");
    }

    @Test
    void streamOnAnotherUsersConversationYieldsSseErrorNot401() throws Exception {
        long demoConv = createConv(demoToken());

        // admin tente de streamer sur la conversation de demo
        MvcResult result = startStream(adminToken(), demoConv, body("Bonjour"));

        assertThat(result.getResponse().getStatus()).isEqualTo(200);
        assertThat(result.getResponse().getContentAsString(StandardCharsets.UTF_8))
                .contains("Conversation introuvable");
    }
}
