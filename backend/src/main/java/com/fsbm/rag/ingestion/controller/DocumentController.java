package com.fsbm.rag.ingestion.controller;

import com.fsbm.rag.ingestion.service.IngestionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

/**
 * Gestion de l'upload et de la liste des documents de cours.
 *
 * <p>L'upload est réservé aux utilisateurs avec le rôle PROFESSOR ou ADMIN.</p>
 */
@RestController
@RequestMapping("/api/documents")
@RequiredArgsConstructor
public class DocumentController {

    private final IngestionService ingestionService;

    /**
     * Upload un PDF et démarre son ingestion asynchrone.
     *
     * <p>POST /api/documents (multipart/form-data)</p>
     *
     * @param file     fichier PDF
     * @param courseId identifiant du cours associé
     * @param userId   utilisateur authentifié (injecté)
     * @return {@code 202 Accepted} avec l'entité Document créée (statut PENDING)
     */
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @PreAuthorize("hasAnyRole('PROFESSOR', 'ADMIN')")
    public ResponseEntity<?> upload(
            @RequestPart("file") MultipartFile file,
            @RequestParam("courseId") Long courseId,
            @AuthenticationPrincipal Long userId) {
        // TODO: valider l'extension (PDF only), déléguer à ingestionService.ingest()
        throw new UnsupportedOperationException("upload non implémenté");
    }

    /**
     * Retourne la liste des documents d'un cours.
     *
     * <p>GET /api/documents?courseId=X</p>
     *
     * @param courseId filtre par cours
     * @return liste des documents avec leur statut d'ingestion
     */
    @GetMapping
    public ResponseEntity<?> listByCourse(@RequestParam Long courseId) {
        // TODO: déléguer à documentRepository, retourner une PageResponse
        throw new UnsupportedOperationException("listByCourse non implémenté");
    }

    /**
     * Supprime un document et tous ses chunks.
     *
     * <p>DELETE /api/documents/{id}</p>
     *
     * @param documentId identifiant du document
     * @param userId     utilisateur authentifié (vérification de propriété)
     * @return {@code 204 No Content}
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('PROFESSOR', 'ADMIN')")
    public ResponseEntity<Void> delete(
            @PathVariable("id") Long documentId,
            @AuthenticationPrincipal Long userId) {
        // TODO: déléguer à ingestionService.delete()
        throw new UnsupportedOperationException("delete non implémenté");
    }
}
