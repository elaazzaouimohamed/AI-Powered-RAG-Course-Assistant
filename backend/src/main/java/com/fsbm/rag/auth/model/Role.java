package com.fsbm.rag.auth.model;

/**
 * Rôles disponibles dans l'application.
 *
 * <ul>
 *   <li>{@code STUDENT} : accès aux fonctionnalités de chat et de quiz.</li>
 *   <li>{@code PROFESSOR} : accès supplémentaire à l'upload de documents.</li>
 *   <li>{@code ADMIN} : accès complet, y compris la gestion des utilisateurs.</li>
 * </ul>
 */
public enum Role {
    STUDENT,
    PROFESSOR,
    ADMIN
}
