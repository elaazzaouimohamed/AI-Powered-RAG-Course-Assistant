import apiClient from './client.js';

/**
 * Fonctions d'accès à l'API quiz.
 */

/**
 * Génère un quiz depuis le contenu d'un cours (réservé PROFESSOR/ADMIN).
 *
 * @param {number} courseId          cours source
 * @param {number} numberOfQuestions nombre de questions (5–20)
 * @returns {Promise<Quiz>} quiz créé avec ses questions
 */
export async function generateQuiz(courseId, numberOfQuestions) {
  const { data } = await apiClient.post('/quizzes/generate', null, {
    params: { courseId, numberOfQuestions },
  });
  return data;
}

/**
 * Récupère les quiz d'un cours.
 *
 * @param {number} courseId identifiant du cours
 * @returns {Promise<Quiz[]>}
 */
export async function fetchQuizzesByCourse(courseId) {
  const { data } = await apiClient.get('/quizzes', { params: { courseId } });
  return data;
}

/**
 * Soumet les réponses d'un étudiant pour un quiz.
 *
 * @param {number} quizId           identifiant du quiz
 * @param {number[]} selectedAnswers indices des réponses choisies
 * @returns {Promise<QuizAttempt>} résultat avec score et corrections
 */
export async function submitQuizAttempt(quizId, selectedAnswers) {
  const { data } = await apiClient.post(`/quizzes/${quizId}/attempts`, selectedAnswers);
  return data;
}
