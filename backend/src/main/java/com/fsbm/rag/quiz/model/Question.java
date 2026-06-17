package com.fsbm.rag.quiz.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * Question à choix multiple appartenant à un {@link Quiz}.
 *
 * <p>Les choix sont stockés comme liste de chaînes dans une colonne JSON.
 * Le champ {@code correctAnswerIndex} désigne l'indice (0-based) de la bonne réponse.</p>
 */
@Entity
@Table(name = "questions")
@Getter
@Setter
@NoArgsConstructor
public class Question {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "quiz_id", nullable = false)
    private Quiz quiz;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String questionText;

    /** Liste des choix de réponse (JSON array) — typiquement 4 options. */
    @Column(nullable = false, columnDefinition = "jsonb")
    private List<String> choices;

    @Column(nullable = false)
    private int correctAnswerIndex;

    /** Explication optionnelle affichée après la réponse de l'étudiant. */
    @Column(columnDefinition = "TEXT")
    private String explanation;
}
