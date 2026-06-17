package com.fsbm.rag.quiz.controller;

import com.fsbm.rag.quiz.service.QuizService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Endpoints de gestion des quiz.
 */
@RestController
@RequestMapping("/api/quizzes")
@RequiredArgsConstructor
public class QuizController {

    private final QuizService quizService;

    /**
     * Génère un quiz depuis le contenu d'un cours.
     *
     * <p>POST /api/quizzes/generate</p>
     *
     * @param courseId          cours source
     * @param numberOfQuestions nombre de questions (5–20)
     * @param userId            professeur authentifié
     * @return {@code 201 Created} avec le quiz généré
     */
    @PostMapping("/generate")
    @PreAuthorize("hasAnyRole('PROFESSOR', 'ADMIN')")
    public ResponseEntity<?> generate(
            @RequestParam Long courseId,
            @RequestParam @Min(5) @Max(20) int numberOfQuestions,
            @AuthenticationPrincipal Long userId) {
        // TODO: déléguer à quizService.generateQuiz()
        throw new UnsupportedOperationException("generate non implémenté");
    }

    /**
     * Retourne les quiz d'un cours.
     *
     * <p>GET /api/quizzes?courseId=X</p>
     *
     * @param courseId filtre par cours
     * @return liste paginée des quiz
     */
    @GetMapping
    public ResponseEntity<?> listByCourse(@RequestParam Long courseId) {
        // TODO: déléguer à quizRepository avec pagination
        throw new UnsupportedOperationException("listByCourse non implémenté");
    }

    /**
     * Soumet les réponses d'un étudiant et retourne son score.
     *
     * <p>POST /api/quizzes/{id}/attempts</p>
     *
     * @param quizId          identifiant du quiz
     * @param selectedAnswers liste des indices de réponses choisies
     * @param userId          étudiant authentifié
     * @return {@code 200 OK} avec le score et les corrections
     */
    @PostMapping("/{id}/attempts")
    public ResponseEntity<?> submitAttempt(
            @PathVariable("id") Long quizId,
            @RequestBody List<Integer> selectedAnswers,
            @AuthenticationPrincipal Long userId) {
        // TODO: déléguer à quizService.submitAttempt()
        throw new UnsupportedOperationException("submitAttempt non implémenté");
    }
}
