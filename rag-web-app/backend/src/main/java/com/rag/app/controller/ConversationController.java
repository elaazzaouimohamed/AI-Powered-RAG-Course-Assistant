package com.rag.app.controller;

import com.rag.app.dto.ConversationDto;
import com.rag.app.dto.MessageDto;
import com.rag.app.service.ConversationService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/conversations")
@RequiredArgsConstructor
public class ConversationController {

    private final ConversationService convService;

    @GetMapping
    public List<ConversationDto> list(@AuthenticationPrincipal UserDetails user) {
        return convService.listForUser(user.getUsername());
    }

    @PostMapping
    public ResponseEntity<ConversationDto> create(
            @AuthenticationPrincipal UserDetails user,
            @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(convService.create(
                user.getUsername(),
                body.get("course"),
                body.get("backend"),
                body.get("model")));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ConversationDto> get(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails user) {
        return ResponseEntity.ok(convService.get(id, user.getUsername()));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<ConversationDto> rename(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails user,
            @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(convService.rename(id, user.getUsername(), body.get("title")));
    }

    @PutMapping("/{convId}/messages/{msgId}")
    public ResponseEntity<MessageDto> editMessage(
            @PathVariable Long convId,
            @PathVariable Long msgId,
            @AuthenticationPrincipal UserDetails user,
            @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(convService.editMessage(convId, user.getUsername(), msgId, body.get("content")));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails user) {
        convService.delete(id, user.getUsername());
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping
    public ResponseEntity<Void> deleteAll(@AuthenticationPrincipal UserDetails user) {
        convService.deleteAll(user.getUsername());
        return ResponseEntity.noContent().build();
    }
}
