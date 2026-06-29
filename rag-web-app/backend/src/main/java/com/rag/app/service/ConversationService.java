package com.rag.app.service;

import com.rag.app.dto.ConversationDto;
import com.rag.app.dto.MessageDto;
import com.rag.app.exception.ResourceNotFoundException;
import com.rag.app.model.*;
import com.rag.app.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ConversationService {

    private final ConversationRepository convRepo;
    private final MessageRepository msgRepo;
    private final UserRepository userRepo;

    public List<ConversationDto> listForUser(String username) {
        User user = getUser(username);
        return convRepo.findByUserIdOrderByUpdatedAtDesc(user.getId())
                .stream().map(c -> toDto(c, false)).collect(Collectors.toList());
    }

    @Transactional
    public ConversationDto create(String username, String course,
                                   String backend, String model) {
        User user = getUser(username);
        Conversation conv = convRepo.save(Conversation.builder()
                .user(user).course(course).backend(backend).model(model).build());
        return toDto(conv, true);
    }

    public ConversationDto get(Long id, String username) {
        Conversation conv = getConv(id, username);
        List<Message> msgs = msgRepo.findByConversationIdOrderByCreatedAtAsc(id);
        ConversationDto dto = toDto(conv, false);
        dto.setMessages(msgs.stream().map(this::toMsgDto).collect(Collectors.toList()));
        return dto;
    }

    @Transactional
    public ConversationDto rename(Long id, String username, String title) {
        Conversation conv = getConv(id, username);
        if (title != null && !title.isBlank()) {
            conv.setTitle(title.length() > 80 ? title.substring(0, 80) : title.trim());
            convRepo.save(conv);
        }
        return toDto(conv, false);
    }

    /** Vérifie que la conversation appartient bien à l'utilisateur (sinon 4xx). */
    public void assertOwnership(Long id, String username) {
        getConv(id, username);
    }

    @Transactional
    public void delete(Long id, String username) {
        Conversation conv = getConv(id, username);
        convRepo.delete(conv);
    }

    @Transactional
    public void deleteAll(String username) {
        User user = getUser(username);
        convRepo.findByUserIdOrderByUpdatedAtDesc(user.getId())
                .forEach(convRepo::delete);
    }

    @Transactional
    public Message addMessage(Long convId, String username, String role, String content) {
        Conversation conv = getConv(convId, username);
        Message msg = msgRepo.save(Message.builder()
                .conversation(conv).role(role).content(content).build());
        conv.setUpdatedAt(LocalDateTime.now());
        if ("user".equals(role) && conv.getTitle().equals("Nouvelle conversation")) {
            conv.setTitle(content.length() > 50 ? content.substring(0, 50) + "…" : content);
        }
        convRepo.save(conv);
        return msg;
    }

    /**
     * Modifie le contenu d'un message utilisateur et supprime tout ce qui suit
     * dans la conversation (les réponses générées à partir de l'ancien contenu
     * deviennent invalides). Le client doit ensuite relancer la génération.
     */
    @Transactional
    public MessageDto editMessage(Long convId, String username, Long messageId, String newContent) {
        if (newContent == null || newContent.isBlank())
            throw new IllegalArgumentException("Le message ne peut pas être vide.");
        Conversation conv = getConv(convId, username);
        Message msg = msgRepo.findById(messageId)
                .filter(m -> m.getConversation().getId().equals(conv.getId()))
                .orElseThrow(() -> new ResourceNotFoundException("Message introuvable"));
        if (!"user".equals(msg.getRole()))
            throw new IllegalArgumentException("Seuls vos propres messages peuvent être modifiés.");

        msg.setContent(newContent.trim());
        msgRepo.save(msg);
        msgRepo.deleteAll(msgRepo.findByConversationIdAndIdGreaterThan(convId, messageId));

        conv.setUpdatedAt(LocalDateTime.now());
        convRepo.save(conv);
        return toMsgDto(msg);
    }

    private Conversation getConv(Long id, String username) {
        User user = getUser(username);
        return convRepo.findById(id)
                .filter(c -> c.getUser().getId().equals(user.getId()))
                .orElseThrow(() -> new ResourceNotFoundException("Conversation introuvable ou accès refusé"));
    }

    private User getUser(String username) {
        return userRepo.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("Utilisateur introuvable"));
    }

    private ConversationDto toDto(Conversation c, boolean includeMessages) {
        return ConversationDto.builder()
                .id(c.getId()).title(c.getTitle()).course(c.getCourse())
                .backend(c.getBackend()).model(c.getModel())
                .createdAt(c.getCreatedAt()).updatedAt(c.getUpdatedAt())
                .messages(includeMessages ? List.of() : null)
                .build();
    }

    private MessageDto toMsgDto(Message m) {
        return MessageDto.builder()
                .id(m.getId()).role(m.getRole()).content(m.getContent())
                .createdAt(m.getCreatedAt()).build();
    }
}
