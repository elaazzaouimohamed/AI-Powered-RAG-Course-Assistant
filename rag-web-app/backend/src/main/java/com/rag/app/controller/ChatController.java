package com.rag.app.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.rag.app.dto.chat.ChatRequest;
import com.rag.app.service.ChatService;
import com.rag.app.service.ConversationService;
import com.rag.app.service.RagService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
public class ChatController {

    private final ChatService chatService;
    private final ConversationService convService;
    private final RagService ragService;
    private final ObjectMapper mapper;

    @Qualifier("sseExecutor")
    private final ThreadPoolTaskExecutor executor;

    /** Drapeaux d'annulation de la génération en cours, par conversation. */
    private final Map<Long, AtomicBoolean> cancelFlags = new ConcurrentHashMap<>();

    @GetMapping("/courses")
    public List<String> getCourses() {
        return ragService.listCourses();
    }

    @PostMapping(value = "/conversations/{convId}/stream",
                 produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream(
            @PathVariable Long convId,
            @RequestBody ChatRequest req,
            @AuthenticationPrincipal UserDetails user) {

        SseEmitter emitter = new SseEmitter(300_000L);

        // IMPORTANT : on N'UTILISE PAS @Valid ni d'exception classique ici.
        // Cet endpoint produit du text/event-stream ; une réponse d'erreur JSON
        // (validation, 404…) ne peut pas être sérialisée pour un Accept SSE et
        // dégénère en 401 trompeur. Toute erreur est donc renvoyée via le canal
        // SSE 'error', que le frontend sait déjà afficher.
        String question = req.getQuestion();
        if (question == null || question.isBlank()) {
            return sseError(emitter, "La question ne peut pas être vide.");
        }

        try {
            convService.assertOwnership(convId, user.getUsername());
        } catch (Exception e) {
            return sseError(emitter, "Conversation introuvable ou accès refusé.");
        }

        // Enregistre le message utilisateur et renvoie immédiatement son ID réel au client
        // (événement SSE 'meta'), pour que le front puisse plus tard l'éditer/le cibler.
        var savedUserMsg = convService.addMessage(convId, user.getUsername(), "user", question);
        try {
            // Encodage JSON par cohérence avec les autres événements SSE (cf. ChatService) —
            // sans risque ici (un ID est numérique), mais garde un seul format de parsing côté front.
            emitter.send(SseEmitter.event().name("meta").data(mapper.writeValueAsString(savedUserMsg.getId().toString())));
        } catch (Exception e) {
            log.warn("Impossible d'envoyer l'événement meta SSE: {}", e.getMessage());
        }

        final AtomicBoolean cancelFlag = new AtomicBoolean(false);
        cancelFlags.put(convId, cancelFlag);

        final String course  = req.getCourse();
        final String backend = req.getBackend();
        final String model   = req.getModel();
        final Double temp    = req.getTemperature();
        executor.submit(() -> {
            try {
                String response = chatService.chat(question, course, backend, model, temp, emitter, cancelFlag);
                if (response != null && !response.isBlank()) {
                    if (cancelFlag.get()) response += "\n\n*(réponse interrompue par l'utilisateur)*";
                    convService.addMessage(convId, user.getUsername(), "assistant", response);
                }
            } finally {
                cancelFlags.remove(convId, cancelFlag);
            }
        });

        return emitter;
    }

    /** Interrompt la génération LLM en cours pour cette conversation. */
    @PostMapping("/conversations/{convId}/stream/stop")
    public ResponseEntity<Void> stop(
            @PathVariable Long convId,
            @AuthenticationPrincipal UserDetails user) {
        convService.assertOwnership(convId, user.getUsername());
        var flag = cancelFlags.get(convId);
        if (flag != null) flag.set(true);
        return ResponseEntity.noContent().build();
    }

    /** Renvoie une erreur via le canal SSE plutôt que par une exception HTTP (cf. stream()). */
    private SseEmitter sseError(SseEmitter emitter, String message) {
        try {
            emitter.send(SseEmitter.event().name("error").data(mapper.writeValueAsString(message)));
            emitter.complete();
        } catch (Exception e) {
            log.warn("Impossible d'envoyer l'erreur SSE: {}", e.getMessage());
        }
        return emitter;
    }
}
