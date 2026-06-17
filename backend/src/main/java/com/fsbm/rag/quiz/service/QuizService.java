package com.fsbm.rag.quiz.service;

import com.fsbm.rag.quiz.model.Quiz;
import com.fsbm.rag.quiz.model.QuizAttempt;

import java.util.List;

/**
 * Service de gestion des quiz : génération, passage et historique.
 */
public interface QuizService {

    /**
     * Génère un quiz automatiquement depuis le contenu d'un cours via le LLM.
     *
     * @param courseId          cours source
     * @param numberOfQuestions nombre de questions à générer
     * @param createdByUserId   professeur demandant la génération
     * @return quiz créé avec ses questions
     */
    Quiz generateQuiz(Long courseId, int numberOfQuestions, Long createdByUserId);

    /**
     * Soumet les réponses d'un étudiant et calcule le score.
     *
     * @param quizId          identifiant du quiz
     * @param studentId       identifiant de l'étudiant
     * @param selectedAnswers liste des indices de réponses choisies
     * @return tentative enregistrée avec le score calculé
     */
    QuizAttempt submitAttempt(Long quizId, Long studentId, List<Integer> selectedAnswers);

    /**
     * Retourne l'historique des tentatives d'un étudiant.
     *
     * @param studentId identifiant de l'étudiant
     * @return liste des tentatives triées par date décroissante
     */
    List<QuizAttempt> getStudentHistory(Long studentId);
}
