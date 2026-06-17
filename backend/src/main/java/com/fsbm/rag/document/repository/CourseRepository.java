package com.fsbm.rag.document.repository;

import com.fsbm.rag.document.model.Course;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Accès aux données des cours.
 */
@Repository
public interface CourseRepository extends JpaRepository<Course, Long> {

    /**
     * Retourne tous les cours d'une matière donnée.
     *
     * @param subjectId identifiant de la matière
     * @return liste des cours
     */
    List<Course> findBySubjectId(Long subjectId);

    /**
     * Retourne tous les cours dispensés par un professeur.
     *
     * @param professorUserId identifiant du professeur
     * @return liste des cours du professeur
     */
    List<Course> findByProfessorUserId(Long professorUserId);
}
