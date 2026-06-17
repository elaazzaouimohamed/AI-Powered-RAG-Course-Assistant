package com.fsbm.rag.ingestion.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * Entité représentant un document PDF uploadé par un professeur.
 *
 * <p>Un document est associé à un cours ({@code course_id}) et possède
 * plusieurs {@link Chunk}s générés lors de l'ingestion.</p>
 */
@Entity
@Table(name = "documents")
@Getter
@Setter
@NoArgsConstructor
public class Document {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String filename;

    /** Chemin de stockage du fichier sur le disque ou dans le bucket S3. */
    @Column(nullable = false)
    private String storagePath;

    @Column(nullable = false)
    private Long courseId;

    /** Uploader : référence l'utilisateur (professeur ou admin). */
    @Column(nullable = false)
    private Long uploadedByUserId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private IngestionStatus status = IngestionStatus.PENDING;

    @Column(nullable = false, updatable = false)
    private Instant uploadedAt = Instant.now();

    /** Nombre de chunks produits lors de l'ingestion (rempli après traitement). */
    private Integer chunkCount;

    public enum IngestionStatus {
        PENDING, PROCESSING, DONE, FAILED
    }
}
