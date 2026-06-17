package com.fsbm.rag.ingestion.service;

import com.fsbm.rag.ingestion.model.Document;
import org.springframework.web.multipart.MultipartFile;

/**
 * Orchestre le pipeline d'ingestion d'un document PDF.
 *
 * <p>Séquence d'opérations :
 * <ol>
 *   <li>Sauvegarde du fichier sur disque (ou stockage objet)</li>
 *   <li>Création de l'entité {@link Document} en base (statut PENDING)</li>
 *   <li>Envoi du fichier au service Python externe (chunking + embedding)</li>
 *   <li>Réception des chunks et de leurs vecteurs, insertion dans pgvector</li>
 *   <li>Mise à jour du statut du document (DONE ou FAILED)</li>
 * </ol>
 * </p>
 */
public interface IngestionService {

    /**
     * Démarre l'ingestion d'un fichier PDF de manière asynchrone.
     *
     * @param file     fichier PDF reçu du frontend
     * @param courseId cours auquel rattacher le document
     * @param userId   professeur ayant uploadé le fichier
     * @return entité {@link Document} créée (statut initial PENDING)
     */
    Document ingest(MultipartFile file, Long courseId, Long userId);

    /**
     * Supprime un document et tous ses chunks associés.
     *
     * @param documentId identifiant du document à supprimer
     * @param userId     utilisateur demandant la suppression (vérification de propriété)
     */
    void delete(Long documentId, Long userId);
}
