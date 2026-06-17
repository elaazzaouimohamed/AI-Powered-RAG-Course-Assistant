package com.fsbm.rag.rag.service;

import com.fsbm.rag.ingestion.model.Chunk;

import java.util.List;

/**
 * Service de recherche sémantique dans la base vectorielle.
 *
 * <p>Convertit la question en vecteur d'embedding (via le service Python),
 * puis interroge pgvector pour récupérer les chunks les plus proches
 * par similarité cosinus.</p>
 */
public interface RetrievalService {

    /**
     * Récupère les chunks les plus similaires à la question posée.
     *
     * @param question question en langage naturel
     * @param courseId filtre sur un cours particulier ({@code null} = tous les cours)
     * @param topK     nombre maximum de chunks à retourner
     * @return liste de chunks triés par score de similarité décroissant
     */
    List<Chunk> findRelevantChunks(String question, Long courseId, int topK);
}
