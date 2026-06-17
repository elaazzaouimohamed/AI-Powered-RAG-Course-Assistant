package com.fsbm.rag.quiz.repository;

import com.fsbm.rag.quiz.model.Quiz;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/**
 * Accès aux données des quiz.
 */
@Repository
public interface QuizRepository extends JpaRepository<Quiz, Long> {

    /**
     * Retourne les quiz d'un cours, paginés.
     *
     * @param courseId  identifiant du cours
     * @param pageable  paramètres de pagination
     * @return page de quiz
     */
    Page<Quiz> findByCourseId(Long courseId, Pageable pageable);
}
