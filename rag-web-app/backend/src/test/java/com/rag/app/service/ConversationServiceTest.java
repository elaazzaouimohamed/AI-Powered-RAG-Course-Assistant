package com.rag.app.service;

import com.rag.app.dto.ConversationDto;
import com.rag.app.exception.ResourceNotFoundException;
import com.rag.app.model.Conversation;
import com.rag.app.model.Role;
import com.rag.app.model.User;
import com.rag.app.repository.ConversationRepository;
import com.rag.app.repository.MessageRepository;
import com.rag.app.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.lenient;
import static org.mockito.Mockito.when;

/** Tests unitaires de la logique d'appartenance des conversations (isolation entre utilisateurs). */
@ExtendWith(MockitoExtension.class)
class ConversationServiceTest {

    @Mock ConversationRepository convRepo;
    @Mock MessageRepository msgRepo;
    @Mock UserRepository userRepo;

    @InjectMocks ConversationService service;

    private User owner;
    private User intruder;
    private Conversation conv;

    @BeforeEach
    void setUp() {
        owner = User.builder().id(1L).username("owner").email("o@x.com")
                .password("p").role(Role.USER).active(true).build();
        intruder = User.builder().id(2L).username("intruder").email("i@x.com")
                .password("p").role(Role.USER).active(true).build();
        conv = Conversation.builder().id(10L).user(owner).title("Conv").build();
    }

    @Test
    void ownerCanAccessTheirConversation() {
        when(userRepo.findByUsername("owner")).thenReturn(Optional.of(owner));
        when(convRepo.findById(10L)).thenReturn(Optional.of(conv));
        when(msgRepo.findByConversationIdOrderByCreatedAtAsc(10L)).thenReturn(java.util.List.of());

        ConversationDto dto = service.get(10L, "owner");

        assertThat(dto.getId()).isEqualTo(10L);
    }

    @Test
    void intruderCannotAccessSomeoneElsesConversation() {
        when(userRepo.findByUsername("intruder")).thenReturn(Optional.of(intruder));
        when(convRepo.findById(10L)).thenReturn(Optional.of(conv));

        assertThatThrownBy(() -> service.get(10L, "intruder"))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void assertOwnershipPassesForOwnerAndFailsForIntruder() {
        when(userRepo.findByUsername("owner")).thenReturn(Optional.of(owner));
        when(userRepo.findByUsername("intruder")).thenReturn(Optional.of(intruder));
        when(convRepo.findById(10L)).thenReturn(Optional.of(conv));

        // Ne lève rien pour le propriétaire
        service.assertOwnership(10L, "owner");

        // Lève pour l'intrus
        assertThatThrownBy(() -> service.assertOwnership(10L, "intruder"))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void unknownUserIsRejected() {
        when(userRepo.findByUsername("ghost")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.assertOwnership(10L, "ghost"))
                .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    void accessingMissingConversationFails() {
        lenient().when(userRepo.findByUsername("owner")).thenReturn(Optional.of(owner));
        when(convRepo.findById(any())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.assertOwnership(999L, "owner"))
                .isInstanceOf(ResourceNotFoundException.class);
    }
}
