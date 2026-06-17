package com.fsbm.rag.ingestion.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

/**
 * Fragment de texte extrait d'un document, associé à son vecteur d'embedding.
 *
 * <p>L'embedding est stocké dans la colonne {@code embedding} de type {@code vector(1536)}
 * grâce à l'extension pgvector. La recherche se fait par similarité cosinus.</p>
 */
@Entity
@Table(name = "chunks")
@Getter
@Setter
@NoArgsConstructor
public class Chunk {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "document_id", nullable = false)
    private Document document;

    /** Contenu textuel du chunk (typiquement 200-500 tokens). */
    @Column(nullable = false, columnDefinition = "TEXT")
    private String content;

    /** Numéro de page du document source (utile pour la citation de sources). */
    private Integer pageNumber;

    /** Indice du chunk dans le document source (ordre de lecture). */
    @Column(nullable = false)
    private Integer chunkIndex;

    /**
     * Vecteur d'embedding stocké comme {@code float[]} mappé sur {@code vector(N)} pgvector.
     * La dimension est définie par le modèle d'embedding utilisé.
     */
    @Column(columnDefinition = "vector(1536)")
    private float[] embedding;
}
