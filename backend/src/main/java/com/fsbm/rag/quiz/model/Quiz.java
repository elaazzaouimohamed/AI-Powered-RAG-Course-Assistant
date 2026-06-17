package com.fsbm.rag.quiz.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

/**
 * Entité représentant un quiz généré depuis le contenu d'un cours.
 *
 * <p>Un quiz appartient à un cours et contient plusieurs {@link Question}s.
 * Il peut être généré automatiquement via le LLM ou créé manuellement
 * par un professeur.</p>
 */
@Entity
@Table(name = "quizzes")
@Getter
@Setter
@NoArgsConstructor
public class Quiz {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false)
    private Long courseId;

    /** Professeur ou admin ayant créé le quiz. */
    @Column(nullable = false)
    private Long createdByUserId;

    @Column(nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    @OneToMany(mappedBy = "quiz", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Question> questions = new ArrayList<>();
}
