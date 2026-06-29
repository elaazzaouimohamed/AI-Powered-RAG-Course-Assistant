package com.rag.app.service;

import com.rag.app.dto.admin.*;
import com.rag.app.model.*;
import com.rag.app.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class AdminService {

    private final UserRepository userRepo;
    private final ConversationRepository convRepo;
    private final MessageRepository msgRepo;
    private final LlmConfigRepository llmRepo;

    public StatsDto getStats() {
        return StatsDto.builder()
                .totalUsers(userRepo.count())
                .totalConversations(convRepo.count())
                .totalMessages(msgRepo.count())
                .activeUsers(userRepo.findAll().stream().filter(User::isActive).count())
                .enabledLlms(llmRepo.findByEnabledTrue().size())
                .build();
    }

    public List<UserAdminDto> getAllUsers() {
        return userRepo.findAll().stream().map(this::toUserDto).collect(Collectors.toList());
    }

    @Transactional
    public UserAdminDto updateUser(Long id, boolean active, Role role) {
        User user = userRepo.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Utilisateur introuvable"));
        // Empêche la suppression du dernier administrateur (rétrogradation/désactivation)
        if (user.getRole() == Role.ADMIN && (role != Role.ADMIN || !active)
                && countActiveAdmins() <= 1) {
            throw new IllegalArgumentException("Impossible : c'est le dernier administrateur actif.");
        }
        user.setActive(active);
        user.setRole(role);
        userRepo.save(user);
        return toUserDto(user);
    }

    @Transactional
    public void deleteUser(Long id) {
        User user = userRepo.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Utilisateur introuvable"));
        if (user.getRole() == Role.ADMIN && countActiveAdmins() <= 1) {
            throw new IllegalArgumentException("Impossible de supprimer le dernier administrateur.");
        }
        userRepo.deleteById(id);
    }

    /** Empêche un admin d'agir sur son propre compte (auto-suppression / rétrogradation). */
    public void assertNotSelf(Long targetId, String currentUsername, String message) {
        userRepo.findByUsername(currentUsername)
                .filter(u -> u.getId().equals(targetId))
                .ifPresent(u -> { throw new IllegalArgumentException(message); });
    }

    private long countActiveAdmins() {
        return userRepo.findAll().stream()
                .filter(u -> u.getRole() == Role.ADMIN && u.isActive()).count();
    }

    // ----- LLM configs -----

    public List<LlmConfigDto> getAllLlms() {
        return llmRepo.findAll().stream().map(this::toDto).collect(Collectors.toList());
    }

    /** Liste publique (sans clé API) des modèles activés, pour le sélecteur du chat. */
    public List<LlmConfigDto> getEnabledLlms() {
        return llmRepo.findByEnabledTrueOrderByIsDefaultDesc().stream()
                .map(this::toPublicDto).collect(Collectors.toList());
    }

    @Transactional
    public LlmConfigDto createLlm(LlmConfigDto dto) {
        if (dto.isDefault()) clearDefaults();
        LlmConfig cfg = llmRepo.save(LlmConfig.builder()
                .name(dto.getName()).backend(dto.getBackend()).model(dto.getModel())
                .baseUrl(blankToNull(dto.getBaseUrl())).apiKey(blankToNull(dto.getApiKey()))
                .temperature(dto.getTemperature() != null ? dto.getTemperature() : 0.3)
                .maxTokens(dto.getMaxTokens() != null ? dto.getMaxTokens() : 2048)
                .enabled(dto.isEnabled()).isDefault(dto.isDefault()).build());
        return toDto(cfg);
    }

    @Transactional
    public LlmConfigDto updateLlm(Long id, LlmConfigDto dto) {
        LlmConfig cfg = llmRepo.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Modèle LLM introuvable"));
        if (dto.isDefault() && !cfg.isDefault()) clearDefaults();
        cfg.setName(dto.getName());
        cfg.setBackend(dto.getBackend());
        cfg.setModel(dto.getModel());
        cfg.setBaseUrl(blankToNull(dto.getBaseUrl()));
        // "****" = masque renvoyé par l'API : ne pas écraser la vraie clé
        if (dto.getApiKey() != null && !dto.getApiKey().isBlank() && !dto.getApiKey().equals("****"))
            cfg.setApiKey(dto.getApiKey());
        if (dto.getTemperature() != null) cfg.setTemperature(dto.getTemperature());
        if (dto.getMaxTokens() != null)   cfg.setMaxTokens(dto.getMaxTokens());
        cfg.setEnabled(dto.isEnabled());
        cfg.setDefault(dto.isDefault());
        return toDto(llmRepo.save(cfg));
    }

    @Transactional
    public void deleteLlm(Long id) { llmRepo.deleteById(id); }

    /** Garantit l'unicité du modèle par défaut. */
    private void clearDefaults() {
        llmRepo.findByIsDefaultTrue().forEach(c -> { c.setDefault(false); llmRepo.save(c); });
    }

    private String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }

    private UserAdminDto toUserDto(User u) {
        return UserAdminDto.builder()
                .id(u.getId()).username(u.getUsername()).email(u.getEmail())
                .role(u.getRole()).active(u.isActive()).createdAt(u.getCreatedAt())
                .conversationCount(convRepo.countByUserId(u.getId()))
                .build();
    }

    private LlmConfigDto toDto(LlmConfig c) {
        return LlmConfigDto.builder()
                .id(c.getId()).name(c.getName()).backend(c.getBackend())
                .model(c.getModel()).baseUrl(c.getBaseUrl())
                .apiKey(c.getApiKey() != null ? "****" : null)
                .temperature(c.getTemperature()).maxTokens(c.getMaxTokens())
                .enabled(c.isEnabled()).isDefault(c.isDefault()).build();
    }

    /** Variante exposée aux utilisateurs : aucune information sensible. */
    private LlmConfigDto toPublicDto(LlmConfig c) {
        return LlmConfigDto.builder()
                .id(c.getId()).name(c.getName()).backend(c.getBackend())
                .model(c.getModel())
                .enabled(c.isEnabled()).isDefault(c.isDefault()).build();
    }
}
