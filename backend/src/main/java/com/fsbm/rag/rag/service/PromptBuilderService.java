package com.fsbm.rag.rag.service;

import com.fsbm.rag.ingestion.model.Chunk;

import java.util.List;

/**
 * Construit le prompt final envoyé au LLM en combinant contexte et question.
 *
 * <p>Le prompt inclut :
 * <ol>
 *   <li>une instruction système définissant le rôle du LLM (tuteur pédagogique en français)</li>
 *   <li>les chunks récupérés par {@code RetrievalService} comme contexte documentaire</li>
 *   <li>la question de l'étudiant</li>
 * </ol>
 * </p>
 */
public interface PromptBuilderService {

    /**
     * Assemble le prompt complet à envoyer au LLM.
     *
     * @param question question de l'étudiant
     * @param chunks   chunks récupérés par la recherche vectorielle
     * @return prompt formaté prêt à être transmis au provider LLM
     */
    String buildRagPrompt(String question, List<Chunk> chunks);

    /**
     * Assemble un prompt pour la génération automatique de questions de quiz.
     *
     * @param courseContent extrait du contenu de cours
     * @param numberOfQuestions nombre de questions à générer
     * @return prompt formaté pour la génération de quiz
     */
    String buildQuizGenerationPrompt(String courseContent, int numberOfQuestions);
}
