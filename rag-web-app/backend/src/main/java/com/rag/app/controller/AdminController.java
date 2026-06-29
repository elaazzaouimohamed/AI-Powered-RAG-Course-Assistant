package com.rag.app.controller;

import com.rag.app.dto.admin.*;
import com.rag.app.model.Role;
import com.rag.app.service.AdminService;
import com.rag.app.service.CourseAdminService;
import com.rag.app.service.RagService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
@PreAuthorize("hasRole('ADMIN')")
@RequiredArgsConstructor
public class AdminController {

    private final AdminService adminService;
    private final CourseAdminService courseAdminService;
    private final RagService ragService;

    @GetMapping("/stats")
    public StatsDto getStats() { return adminService.getStats(); }

    @GetMapping("/users")
    public List<UserAdminDto> getUsers() { return adminService.getAllUsers(); }

    @PutMapping("/users/{id}")
    public ResponseEntity<UserAdminDto> updateUser(
            @PathVariable Long id,
            @RequestBody Map<String, Object> body,
            @AuthenticationPrincipal UserDetails current) {
        boolean active = (Boolean) body.getOrDefault("active", true);
        Role role = Role.valueOf((String) body.getOrDefault("role", "USER"));
        adminService.assertNotSelf(id, current.getUsername(),
                "Vous ne pouvez pas modifier votre propre compte ici.");
        return ResponseEntity.ok(adminService.updateUser(id, active, role));
    }

    @DeleteMapping("/users/{id}")
    public ResponseEntity<Void> deleteUser(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails current) {
        adminService.assertNotSelf(id, current.getUsername(),
                "Vous ne pouvez pas supprimer votre propre compte.");
        adminService.deleteUser(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/llms")
    public List<LlmConfigDto> getLlms() { return adminService.getAllLlms(); }

    @PostMapping("/llms")
    public ResponseEntity<LlmConfigDto> createLlm(@RequestBody LlmConfigDto dto) {
        return ResponseEntity.ok(adminService.createLlm(dto));
    }

    @PutMapping("/llms/{id}")
    public ResponseEntity<LlmConfigDto> updateLlm(
            @PathVariable Long id, @RequestBody LlmConfigDto dto) {
        return ResponseEntity.ok(adminService.updateLlm(id, dto));
    }

    @DeleteMapping("/llms/{id}")
    public ResponseEntity<Void> deleteLlm(@PathVariable Long id) {
        adminService.deleteLlm(id);
        return ResponseEntity.noContent().build();
    }

    // ----- Cours (ingestion RAG) -----

    @GetMapping("/courses")
    public List<String> getCourses() { return ragService.listCourses(); }

    @PostMapping(value = "/courses/upload", consumes = "multipart/form-data")
    public ResponseEntity<Map<String, Object>> uploadCourse(
            @RequestParam("courseName") String courseName,
            @RequestParam("file") MultipartFile file) {
        return ResponseEntity.ok(courseAdminService.uploadCourse(courseName, file));
    }

    @GetMapping("/courses/jobs/{jobId}")
    public ResponseEntity<Map<String, Object>> getJobStatus(@PathVariable String jobId) {
        return ResponseEntity.ok(courseAdminService.getJobStatus(jobId));
    }

    @DeleteMapping("/courses/{courseName}")
    public ResponseEntity<Void> deleteCourse(@PathVariable String courseName) {
        courseAdminService.deleteCourse(courseName);
        return ResponseEntity.noContent().build();
    }
}
