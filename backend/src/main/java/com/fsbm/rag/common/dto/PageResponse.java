package com.fsbm.rag.common.dto;

import java.util.List;

/**
 * Enveloppe de réponse paginée générique.
 *
 * <p>Utilisée par tous les endpoints qui retournent des listes paginées,
 * assurant un format JSON uniforme côté frontend.</p>
 *
 * @param <T>        type des éléments de la page
 * @param content    éléments de la page courante
 * @param page       numéro de page courant (0-based)
 * @param size       taille de la page
 * @param totalElements nombre total d'éléments dans la collection
 * @param totalPages nombre total de pages
 */
public record PageResponse<T>(
    List<T> content,
    int page,
    int size,
    long totalElements,
    int totalPages
) {
    /**
     * Construit un {@code PageResponse} depuis un objet Spring Data {@code Page}.
     *
     * @param springPage page Spring Data
     * @param <T>        type des éléments
     * @return instance de {@code PageResponse}
     */
    public static <T> PageResponse<T> from(org.springframework.data.domain.Page<T> springPage) {
        return new PageResponse<>(
            springPage.getContent(),
            springPage.getNumber(),
            springPage.getSize(),
            springPage.getTotalElements(),
            springPage.getTotalPages()
        );
    }
}
