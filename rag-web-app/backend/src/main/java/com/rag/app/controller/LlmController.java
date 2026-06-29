package com.rag.app.controller;

import com.rag.app.dto.admin.LlmConfigDto;
import com.rag.app.service.AdminService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * Liste publique (utilisateurs authentifiés) des modèles LLM activés.
 * Permet au chat de proposer un sélecteur de modèles sans exposer les clés API
 * ni nécessiter le rôle ADMIN.
 */
@RestController
@RequestMapping("/api/llms")
@RequiredArgsConstructor
public class LlmController {

    private final AdminService adminService;

    @GetMapping
    public List<LlmConfigDto> enabledLlms() {
        return adminService.getEnabledLlms();
    }
}
