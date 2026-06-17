package com.fsbm.rag.common.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Gestionnaire global des exceptions — centralise le format des réponses d'erreur.
 *
 * <p>Utilise le standard RFC 7807 ({@code ProblemDetail}) pour les réponses d'erreur,
 * ce qui facilite la gestion côté frontend.</p>
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * Gère les erreurs de validation des DTOs ({@code @Valid}).
     *
     * @param ex exception de validation Spring
     * @return {@code 400 Bad Request} avec le détail des champs invalides
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        // TODO: construire un ProblemDetail avec la liste des erreurs de champ
        throw new UnsupportedOperationException("handleValidation non implémenté");
    }

    /**
     * Gère les ressources introuvables.
     *
     * @param ex exception métier
     * @return {@code 404 Not Found}
     */
    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex) {
        // TODO: retourner ProblemDetail avec status 404 et le message de l'exception
        throw new UnsupportedOperationException("handleNotFound non implémenté");
    }

    /**
     * Gère les accès non autorisés.
     *
     * @param ex exception métier
     * @return {@code 401 Unauthorized}
     */
    @ExceptionHandler(UnauthorizedException.class)
    public ProblemDetail handleUnauthorized(UnauthorizedException ex) {
        // TODO: retourner ProblemDetail avec status 401
        throw new UnsupportedOperationException("handleUnauthorized non implémenté");
    }

    /**
     * Filet de sécurité : capture toute exception non prévue.
     *
     * @param ex exception quelconque
     * @return {@code 500 Internal Server Error} sans exposer la stack trace
     */
    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneric(Exception ex) {
        // TODO: logger l'exception, retourner un message générique sans détails internes
        return ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR,
                "Une erreur interne s'est produite");
    }

    // ── Exceptions métier ───────────────────────────────────────────────────

    public static class ResourceNotFoundException extends RuntimeException {
        public ResourceNotFoundException(String message) { super(message); }
    }

    public static class UnauthorizedException extends RuntimeException {
        public UnauthorizedException(String message) { super(message); }
    }

    public static class ConflictException extends RuntimeException {
        public ConflictException(String message) { super(message); }
    }
}
