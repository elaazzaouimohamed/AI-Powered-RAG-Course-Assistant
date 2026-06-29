package com.rag.app.service;

import com.rag.app.repository.LlmConfigRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/** Tests unitaires du grounding strict : sans contexte de cours, le LLM n'est jamais sollicité. */
@ExtendWith(MockitoExtension.class)
class ChatServiceTest {

    @Mock RagService ragService;
    @Mock LlmConfigRepository llmRepo;

    @Test
    void withoutAnyCourseContextItRefusesWithoutCallingTheLlm() throws Exception {
        var chatService = new ChatService(ragService, llmRepo);
        when(ragService.retrieveContexts(any(), any())).thenReturn(List.of());

        SseEmitter emitter = mock(SseEmitter.class);
        String result = chatService.chat("Question hors sujet", "", "lmstudio", null, emitter);

        // Message de refus renvoyé, sans aucune configuration LLM consultée
        assertThat(result).contains("Je ne trouve pas cette information");
        verifyNoInteractions(llmRepo);

        // Le flux SSE a bien reçu le message puis l'événement de fin
        verify(emitter, atLeastOnce()).send(any(SseEmitter.SseEventBuilder.class));
        verify(emitter).complete();
    }

    @Test
    void emptyContextShortCircuitsRegardlessOfBackend() {
        var chatService = new ChatService(ragService, llmRepo);
        when(ragService.retrieveContexts(any(), any())).thenReturn(List.of());

        for (String backend : List.of("lmstudio", "ollama", "nvidia", "")) {
            SseEmitter emitter = mock(SseEmitter.class);
            String result = chatService.chat("q", "cours", backend, null, emitter);
            assertThat(result).contains("Je ne trouve pas cette information");
        }
        // Aucune config LLM n'est jamais chargée puisqu'on court-circuite avant l'appel
        verifyNoInteractions(llmRepo);
    }

    @Test
    void retrievalIsAlwaysAttemptedWithTheQuestionAndCourse() {
        var chatService = new ChatService(ragService, llmRepo);
        when(ragService.retrieveContexts(eq("Quest ce que la variance"), eq("Stat")))
                .thenReturn(List.<Map<String, String>>of());

        chatService.chat("Quest ce que la variance", "Stat", "lmstudio", null, mock(SseEmitter.class));

        verify(ragService).retrieveContexts("Quest ce que la variance", "Stat");
    }
}
