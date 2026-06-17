/**
 * Affiche le résultat final d'un quiz après soumission.
 *
 * Montre :
 *   - le score (en pourcentage et en fraction x/total)
 *   - une appréciation textuelle selon le score
 *   - un bouton pour relancer le quiz ou retourner au chat
 *
 * @param {object}   props
 * @param {number}   props.score         - score en pourcentage (0–100)
 * @param {number}   props.totalQuestions - nombre total de questions
 * @param {number}   props.correctCount  - nombre de bonnes réponses
 * @param {Function} props.onRetry       - appelé pour relancer le quiz
 * @param {Function} props.onClose       - appelé pour fermer / retourner au chat
 */
export default function QuizResult({ score, totalQuestions, correctCount, onRetry, onClose }) {
  function getAppreciation(score) {
    if (score >= 80) return 'Excellent travail !';
    if (score >= 60) return 'Bien joué, continuez ainsi.';
    if (score >= 40) return 'Pas mal, mais vous pouvez progresser.';
    return 'Continuez à réviser ce chapitre.';
  }

  return (
    <div className="quiz-result">
      {/* Score circulaire ou barre — TODO: remplacer par un vrai graphique */}
      <div className="quiz-result__score">{score}%</div>

      <p className="quiz-result__detail">
        {correctCount} / {totalQuestions} bonnes réponses
      </p>

      <p className="quiz-result__appreciation">{getAppreciation(score)}</p>

      <div className="quiz-result__actions">
        <button className="quiz-result__btn quiz-result__btn--retry" onClick={onRetry}>
          Réessayer
        </button>
        <button className="quiz-result__btn quiz-result__btn--close" onClick={onClose}>
          Retour au chat
        </button>
      </div>
    </div>
  );
}
