package com.fsbm.rag.ingestion.repository;

import com.fsbm.rag.ingestion.model.Document;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Accès aux données des documents uploadés.
 */
@Repository
public interface DocumentRepository extends JpaRepository<Document, Long> {

    /**
     * Retourne tous les documents d'un cours donné.
     *
     * @param courseId identifiant du cours
     * @return liste des documents appartenant au cours
     */
    List<Document> findByCourseId(Long courseId);

    /**
     * Retourne tous les documents uploadés par un utilisateur.
     *
     * @param userId identifiant de l'uploader
     * @return liste des documents de cet utilisateur
     */
    List<Document> findByUploadedByUserId(Long userId);
}
