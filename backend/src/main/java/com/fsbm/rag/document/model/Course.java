package com.fsbm.rag.document.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.NoArgsConstructor;

/**
 * Cours universitaire auquel sont rattachés des documents et des quiz.
 *
 * <p>Un cours appartient à une {@link Subject} et est dispensé par un professeur
 * (référencé par {@code professorUserId}).</p>
 */
@Entity
@Table(name = "courses")
@Getter
@Setter
@NoArgsConstructor
public class Course {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 150)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String description;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "subject_id")
    private Subject subject;

    @Column(nullable = false)
    private Long professorUserId;

    /** Semestre ou année académique (ex : "S3 2024-2025"). */
    @Column(length = 30)
    private String semester;
}
