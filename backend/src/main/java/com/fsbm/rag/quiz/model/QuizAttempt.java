package com.fsbm.rag.quiz.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;

/**
 * Enregistre une tentative de quiz par un étudiant.
 *
 * <p>Stocke les réponses choisies et le score calculé, permettant
 * d'afficher l'historique des passages et de mesurer la progression.</p>
 */
@Entity
@Table(name = "quiz_attempts")
@Getter
@Setter
@NoArgsConstructor
public class QuizAttempt {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "quiz_id", nullable = false)
    private Quiz quiz;

    @Column(nullable = false)
    private Long studentId;

    /** Indices des réponses choisies (dans le même ordre que les questions). */
    @Column(columnDefinition = "jsonb")
    private List<Integer> selectedAnswers;

    /** Score en pourcentage (0–100). */
    @Column(nullable = false)
    private int score;

    @Column(nullable = false, updatable = false)
    private Instant completedAt = Instant.now();
}
