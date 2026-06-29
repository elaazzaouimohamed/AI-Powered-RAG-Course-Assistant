package com.rag.app.exception;

/** Levée quand une ressource demandée n'existe pas ou n'appartient pas à l'utilisateur. */
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
