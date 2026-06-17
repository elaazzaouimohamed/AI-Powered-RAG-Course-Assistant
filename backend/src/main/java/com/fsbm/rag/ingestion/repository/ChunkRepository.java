package com.fsbm.rag.ingestion.repository;

import com.fsbm.rag.ingestion.model.Chunk;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Accès aux chunks et requêtes de recherche vectorielle via pgvector.
 */
@Repository
public interface ChunkRepository extends JpaRepository<Chunk, Long> {

    /**
     * Recherche les K chunks les plus proches d'un vecteur d'embedding donné.
     *
     * <p>La requête native utilise l'opérateur {@code <=>} de pgvector
     * (distance cosinus). Filtre optionnel sur le cours via une jointure sur
     * la table {@code documents}.</p>
     *
     * @param embedding vecteur de la question (même dimension que les embeddings stockés)
     * @param courseId  filtre par cours ({@code null} pour tous les cours)
     * @param limit     nombre maximum de résultats
     * @return liste de chunks triés par similarité décroissante
     */
    @Query(value = """
            SELECT c.*
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE (:courseId IS NULL OR d.course_id = :courseId)
            ORDER BY c.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """, nativeQuery = true)
    List<Chunk> findTopKBySimilarity(
            @Param("embedding") String embedding,
            @Param("courseId") Long courseId,
            @Param("limit") int limit
    );

    /**
     * Supprime tous les chunks d'un document (avant ré-ingestion).
     *
     * @param documentId identifiant du document
     */
    void deleteByDocumentId(Long documentId);
}
